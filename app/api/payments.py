# backend/app/api/payments.py
import asyncio
import html
import json
import smtplib
from typing import List, Optional
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from fpdf import FPDF

from app.core.config import settings
from app.core.taxes import calculate_order_taxes
from app.models.product import Product, ProductVariant
from app.models.order import Order, OrderItem, OrderStatus
from app.models.user import User
from app.core.db import get_async_session
from app.api.deps import get_optional_user, get_current_admin  # 🔐 Dépendances RBAC

# 🔐 Clé Stripe lue depuis les variables d'environnement (jamais écrite dans le code)
stripe.api_key = settings.STRIPE_SECRET_KEY

router = APIRouter(prefix="/payments", tags=["Payments"])


# ==========================================================================
# 🛠️ OUTILS INTERNES
# ==========================================================================

def _safe(text) -> str:
    """fpdf 1.x n'accepte que le latin-1 : remplace les caractères non supportés."""
    return str(text if text is not None else "").encode("latin-1", "replace").decode("latin-1")


def local_generate_pdf(order: Order, cart_snapshot: list) -> bytes:
    """Génère la facture PDF en mémoire."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "L'ATELIER KAMERSHOES CANADA", ln=True, align="C")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 5, "Confections Artisanales de Maroquinerie de Luxe", ln=True, align="C")
    pdf.cell(0, 5, _safe(f"Facture # ATK-00{order.id} | Province: {order.province_code}"), ln=True, align="C")
    pdf.ln(10)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(110, 7, "Description", border=1)
    pdf.cell(30, 7, "Prix Unit.", border=1, align="C")
    pdf.cell(20, 7, "Qte", border=1, align="C")
    pdf.cell(30, 7, "Total CAD", border=1, align="C")
    pdf.ln()

    pdf.set_font("Helvetica", "", 10)
    for entry in cart_snapshot:
        price = float(entry.get("price_snap") or 0)
        qty = int(entry.get("quantity") or 0)
        pdf.cell(110, 7, _safe(entry.get("product_name")), border=1)
        pdf.cell(30, 7, f"{price:.2f} $", border=1, align="C")
        pdf.cell(20, 7, str(qty), border=1, align="C")
        pdf.cell(30, 7, f"{price * qty:.2f} $", border=1, align="C")
        pdf.ln()

    pdf.ln(5)
    pdf.cell(160, 6, "Montant Total Collecte (Taxes incluses) :", align="R")
    pdf.cell(30, 6, f"{order.total_amount:.2f} $", border=1, align="C", ln=True)

    output = pdf.output(dest="S")
    if isinstance(output, str):  # fpdf 1.x renvoie une chaîne latin-1
        output = output.encode("latin-1")
    return bytes(output)


def _send_email(msg: MIMEMultipart, recipient_email: str) -> None:
    """Envoi SMTP générique (identifiants lus depuis les variables d'environnement)."""
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        raise RuntimeError("SMTP_USER / SMTP_PASSWORD ne sont pas configurés")
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(settings.SMTP_USER, recipient_email, msg.as_string())


# 📧 ENVOI DE LA FACTURE AU CLIENT
def native_send_email(order: Order, cart_snapshot: list, recipient_email: str) -> None:
    try:
        msg = MIMEMultipart()
        msg["From"] = f"L'Atelier Kamershoes <{settings.SMTP_USER}>"
        msg["To"] = recipient_email
        msg["Subject"] = f"🧾 Votre facture de l'Atelier - Commande #ATK-00{order.id}"

        html_body = f"""
        <h3>Bonjour,</h3>
        <p>Félicitations, votre commande <b>ATK-00{order.id}</b> a été validée avec succès !</p>
        <p>Montant total payé : <b>{order.total_amount:.2f} $ CAD</b>.</p>
        <p>Votre facture officielle détaillée est disponible en pièce jointe au format PDF.</p>
        <br/>
        <p>Cordialement,<br/><b>L'Équipe de l'Atelier Kamershoes Canada</b></p>
        """
        msg.attach(MIMEText(html_body, "html"))

        part = MIMEBase("application", "pdf")
        part.set_payload(local_generate_pdf(order, cart_snapshot))
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f"attachment; filename=Facture_Atelier_{order.id}.pdf")
        msg.attach(part)

        _send_email(msg, recipient_email)
        print(f"📧 [SMTP SUCCESS] Facture envoyée pour la commande {order.id}")
    except Exception as err:
        print(f"⚠️ [SMTP ERROR] Échec de l'envoi de la facture : {err}")


# ✈️ ENVOI DE LA NOTIFICATION D'EXPÉDITION
def send_shipping_email(order: Order, recipient_email: str) -> None:
    try:
        tracking = html.escape(str(order.tracking_number or ""))

        msg = MIMEMultipart()
        msg["From"] = f"L'Atelier Kamershoes <{settings.SMTP_USER}>"
        msg["To"] = recipient_email
        msg["Subject"] = f"✈️ Votre colis de l'Atelier est en route ! - Commande #ATK-00{order.id}"

        html_body = f"""
        <h3>Bonjour,</h3>
        <p>Les artisans de l'Atelier ont finalisé la confection de votre commande <b>ATK-00{order.id}</b>.</p>
        <p>Votre colis a été remis à <b>Postes Canada</b> et est officiellement en route vers votre adresse de livraison.</p>
        <div style="background-color: #faf9f6; padding: 15px; border-radius: 12px; border: 1px solid #f1f0ea; margin: 15px 0;">
            <p style="margin: 0; font-size: 13px; color: #1c1917;">🚚 <b>Numéro de suivi officiel :</b> <span style="font-family: monospace; color: #e02424; font-weight: bold;">{tracking}</span></p>
        </div>
        <p>Vous pouvez utiliser ce numéro directement sur le portail de Postes Canada pour suivre l'acheminement de vos souliers en temps réel.</p>
        <br/>
        <p>Merci pour votre confiance,<br/><b>L'Équipe Logistique de l'Atelier Canada</b> 🍁</p>
        """
        msg.attach(MIMEText(html_body, "html"))

        _send_email(msg, recipient_email)
        print(f"✈️ [LOGISTIQUE SUCCESS] Notification d'expédition envoyée pour la commande {order.id}")
    except Exception as err:
        print(f"⚠️ [LOGISTIQUE ERROR] Échec de la notification : {err}")


# ==========================================================================
# 💳 CAISSE
# ==========================================================================

@router.post("/create-payment-intent")
async def create_and_confirm_payment_intent(
    payload: Request,
    session: AsyncSession = Depends(get_async_session),
    current_user: Optional[User] = Depends(get_optional_user),  # facultatif : les clients sans compte peuvent commander
):
    # 🛑 Cette caisse confirme le paiement avec une carte de TEST (tok_visa).
    # Elle ne doit donc jamais tourner avec une clé réelle (sk_live_...).
    if not (settings.STRIPE_SECRET_KEY or "").startswith("sk_test_"):
        raise HTTPException(
            status_code=503,
            detail="Paiement indisponible : la caisse est configurée pour le mode test Stripe uniquement.",
        )

    try:
        body = await payload.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Requête invalide")

    province_code = body.get("province_code")
    items = body.get("items") or []
    customer_name = body.get("fullName", "Client Anonyme")
    shipping_address = body.get("address", "Adresse de Livraison")
    city = body.get("city", "Ville")
    postal_code = body.get("postalCode", "H3B 1A7")
    customer_email = str(body.get("email") or "").strip()

    if not items:
        raise HTTPException(status_code=400, detail="Le panier est vide")

    # ---------- 1. Validation du panier (prix et stock lus côté serveur uniquement) ----------
    lines = []
    reserved = {}
    subtotal = 0.0

    for item in items:
        if not item.get("product_id") or not item.get("variant_id"):
            raise HTTPException(status_code=400, detail="Article invalide dans le panier")
        try:
            quantity = int(item.get("quantity", 1))
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="Quantité invalide")
        if quantity < 1 or quantity > 50:
            raise HTTPException(status_code=400, detail="Quantité invalide")

        product = await session.get(Product, item.get("product_id"))
        if not product or not product.is_active:
            raise HTTPException(status_code=404, detail="Produit introuvable")

        # Verrou de ligne : évite que deux commandes simultanées vendent le même stock
        variant = await session.get(ProductVariant, item.get("variant_id"), with_for_update=True)
        if not variant or getattr(variant, "product_id", product.id) != product.id:
            raise HTTPException(status_code=404, detail="Variante introuvable")

        already = reserved.get(variant.id, 0)
        if variant.stock - already < quantity:
            raise HTTPException(status_code=409, detail=f"Stock insuffisant pour {product.name}")
        reserved[variant.id] = already + quantity

        subtotal += product.price_cad * quantity
        lines.append({"product": product, "variant": variant, "quantity": quantity})

    cart_snapshot = [
        {
            "product_name": line["product"].name,
            "price_snap": line["product"].price_cad,
            "quantity": line["quantity"],
        }
        for line in lines
    ]

    tax_summary = calculate_order_taxes(subtotal, province_code)
    total_with_tax = tax_summary["total_with_tax"]
    amount_in_cents = int(round(total_with_tax * 100))
    if amount_in_cents < 50:  # minimum Stripe : 0,50 CAD
        raise HTTPException(status_code=400, detail="Montant de commande trop faible")

    items_metadata = [
        {"v_id": line["variant"].id, "qty": line["quantity"]} for line in lines
    ]

    # ---------- 2. Paiement Stripe (appel bloquant exécuté hors de la boucle asynchrone) ----------
    try:
        intent = await asyncio.to_thread(
            stripe.PaymentIntent.create,
            amount=amount_in_cents,
            currency="cad",
            payment_method_data={"type": "card", "card": {"token": "tok_visa"}},
            confirm=True,
            automatic_payment_methods={"enabled": True, "allow_redirects": "never"},
            metadata={
                "province_code": str(province_code),
                "subtotal": str(subtotal),
                "cart_items_json": json.dumps(items_metadata),
            },
        )
    except stripe.StripeError as err:
        await session.rollback()
        print(f"⚠️ [STRIPE ERROR] {err}")
        message = getattr(err, "user_message", None) or "Le paiement a été refusé."
        raise HTTPException(status_code=402, detail=message)

    if intent.status != "succeeded":
        await session.rollback()
        raise HTTPException(status_code=402, detail="Le paiement n'a pas abouti.")

    # ---------- 3. Enregistrement de la commande ----------
    try:
        new_order = Order(
            user_id=current_user.id if current_user else None,
            total_amount=total_with_tax,
            tax_amount=tax_summary["tps_amount"] + tax_summary["tvp_amount"] + tax_summary["tvh_amount"],
            province_code=province_code,
            shipping_address=f"{customer_name}, {shipping_address}, {city}, {postal_code}, {customer_email}",
            status=OrderStatus.PAID,
            tracking_number=None,
        )
        session.add(new_order)
        await session.flush()

        for line in lines:
            line["variant"].stock = max(0, line["variant"].stock - line["quantity"])
            session.add(
                OrderItem(
                    order_id=new_order.id,
                    product_id=line["product"].id,
                    variant_id=line["variant"].id,
                    quantity=line["quantity"],
                    price_snap=line["product"].price_cad,
                )
            )

        await session.commit()
    except Exception as err:
        await session.rollback()
        print(f"⚠️ [DB ERROR] Commande non enregistrée après paiement : {err}")
        # Le client a été débité mais la commande n'existe pas : on tente le remboursement
        try:
            await asyncio.to_thread(stripe.Refund.create, payment_intent=intent.id)
            print(f"↩️ Remboursement automatique effectué pour {intent.id}")
        except Exception as refund_err:
            print(f"🚨 REMBOURSEMENT MANUEL REQUIS pour {intent.id} : {refund_err}")
        raise HTTPException(
            status_code=500,
            detail="Une erreur est survenue lors de l'enregistrement de la commande. Contactez-nous si vous avez été débité.",
        )

    # ---------- 4. Facture par e-mail ----------
    # Envoyée avant la réponse : sur Vercel, les tâches d'arrière-plan peuvent être
    # coupées une fois la réponse envoyée. L'échec de l'e-mail n'annule pas la commande.
    if "@" in customer_email:
        await asyncio.to_thread(native_send_email, new_order, cart_snapshot, customer_email)

    print(f"💰 Commande enregistrée avec succès. ID: {new_order.id}")
    return {"success": True, "status": intent.status, "total_to_pay_cad": total_with_tax}


# ==========================================================================
# ✈️ SUIVI LOGISTIQUE ET EXTRACTION ADMINISTRATIVE
# ==========================================================================

@router.get("/admin/orders", response_model=List[Order])
async def list_all_orders_for_admin(
    session: AsyncSession = Depends(get_async_session),
    admin: User = Depends(get_current_admin),
):
    """Extrait l'intégralité des commandes pour l'onglet logistique."""
    statement = select(Order).order_by(Order.id.desc())
    results = await session.exec(statement)
    return results.all()


@router.post("/admin/orders/{order_id}/ship")
async def ship_order_and_notify_client(
    order_id: int,
    payload: Request,
    session: AsyncSession = Depends(get_async_session),
    admin: User = Depends(get_current_admin),
):
    """Enregistre le numéro de suivi, passe la commande en SHIPPED et prévient l'acheteur."""
    try:
        body = await payload.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Requête invalide")

    tracking_number = str(body.get("tracking_number") or "").strip()
    frontend_email = str(body.get("email") or "").strip()

    if not tracking_number or len(tracking_number) > 64:
        raise HTTPException(status_code=400, detail="Le numéro de suivi Postes Canada est requis.")

    order_result = await session.exec(select(Order).where(Order.id == order_id))
    db_order = order_result.one_or_none()

    if not db_order:
        raise HTTPException(status_code=404, detail="Cette facture de commande n'existe pas.")

    db_order.tracking_number = tracking_number
    db_order.status = OrderStatus.SHIPPED
    session.add(db_order)
    await session.commit()

    # 🕵️ Recherche de l'e-mail de l'acheteur
    final_recipient = None

    # Niveau 1 : e-mail envoyé par le tableau de bord
    if "@" in frontend_email:
        final_recipient = frontend_email

    # Niveau 2 : e-mail enregistré dans l'adresse de livraison
    if not final_recipient and db_order.shipping_address:
        found = next((s for s in db_order.shipping_address.split(",") if "@" in s), None)
        if found:
            final_recipient = found.strip()

    # Niveau 3 : adresse de repli configurée
    if not final_recipient:
        final_recipient = settings.ADMIN_EMAIL or settings.SMTP_USER or None

    if final_recipient:
        await asyncio.to_thread(send_shipping_email, db_order, final_recipient)
        detail = f"Commande marquée comme expédiée. Notification transmise à {final_recipient}"
    else:
        detail = "Commande marquée comme expédiée (aucune adresse e-mail disponible pour la notification)."

    print(f"✈️ Logistique validée pour la commande {order_id}")
    return {"success": True, "detail": detail}


# ==========================================================================
# 🪝 WEBHOOK STRIPE
# ==========================================================================

@router.post("/webhook", status_code=status.HTTP_200_OK)
async def stripe_webhook(request: Request):
    """Reçoit les événements Stripe. La signature est vérifiée avant toute acceptation."""
    if not settings.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail="Webhook non configuré")

    raw_body = await request.body()
    signature = request.headers.get("stripe-signature", "")
    try:
        stripe.Webhook.construct_event(raw_body, signature, settings.STRIPE_WEBHOOK_SECRET)
    except Exception:
        raise HTTPException(status_code=400, detail="Signature invalide")

    return {"status": "success"}
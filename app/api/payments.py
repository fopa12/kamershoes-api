# backend/app/api/payments.py
import json
import smtplib
from typing import List, Optional
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, status, BackgroundTasks
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from fpdf import FPDF
from app.core.taxes import calculate_order_taxes
from app.models.product import Product, ProductVariant
from app.models.order import Order, OrderItem, OrderStatus
from app.models.user import User
from app.core.db import get_async_session
from app.api.deps import get_current_user, get_current_admin # 🔐 Extraction des dépendances RBAC

# Clé secrète Stripe fonctionnelle
stripe.api_key = "sk_test_51U6vZARjpaxWnLPeNAzR4WiJ06nxhCnC2w92I4WW0hzFyh4wOKoRXZtKrZSPrTz75bazxRbhM1nwXu1F5wpZHDiT00Qzsuy7Vh"

router = APIRouter(prefix="/payments", tags=["Payments"])

# 🛠️ FONCTION DE GÉNÉRATION PDF PURE (En mémoire)
def local_generate_pdf(order: Order, cart_snapshot: list) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "L'ATELIER KAMERSHOES CANADA", ln=True, align="C")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 5, "Confections Artisanales de Maroquinerie de Luxe", ln=True, align="C")
    pdf.cell(0, 5, f"Facture # ATK-00{order.id} | Province: {order.province_code}", ln=True, align="C")
    pdf.ln(10)
    
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(110, 7, "Description", border=1)
    pdf.cell(30, 7, "Prix Unit.", border=1, align="C")
    pdf.cell(20, 7, "Qte", border=1, align="C")
    pdf.cell(30, 7, "Total CAD", border=1, align="C")
    pdf.ln()
    
    pdf.set_font("Helvetica", "", 10)
    for entry in cart_snapshot:
        pdf.cell(110, 7, str(entry.get("product_name")), border=1)
        pdf.cell(30, 7, f"{entry.get('price_snap'):.2f} $", border=1, align="C")
        pdf.cell(20, 7, str(entry.get("quantity")), border=1, align="C")
        pdf.cell(30, 7, f"{(entry.get('price_snap') * entry.get('quantity')):.2f} $", border=1, align="C")
        pdf.ln()
        
    pdf.ln(5)
    pdf.cell(160, 6, "Montant Total Collecte (Taxes incluses) :", align="R")
    pdf.cell(30, 6, f"{order.total_amount:.2f} $", border=1, align="C", ln=True)
    return pdf.output(dest='S')

# 📧 ENVOI SMTP NATIF (LIVRAISON PERSONNALISÉE SUR LA BOÎTE DU CLIENT)
def native_send_email(order: Order, cart_snapshot: list, recipient_email: str):
    try:
        sender_email = "fopsimella@gmail.com"
        sender_password = "bpvckgsoizztjobs" # Mot de passe d'application Google (16 caractères)
        
        msg = MIMEMultipart()
        msg['From'] = f"L'Atelier Kamershoes <{sender_email}>"
        msg['To'] = recipient_email
        msg['Subject'] = f"🧾 Votre facture de l'Atelier - Commande #ATK-00{order.id}"
        
        html_body = f"""
        <h3>Bonjour,</h3>
        <p>Félicitations, votre commande <b>ATK-00{order.id}</b> a été validée avec succès !</p>
        <p>Montant total payé : <b>{order.total_amount:.2f} $ CAD</b>.</p>
        <p>Votre facture officielle détaillée est disponible en pièce jointe au format PDF.</p>
        <br/>
        <p>Cordialement,<br/><b>L'Équipe de l'Atelier Kamershoes Canada</b></p>
        """
        msg.attach(MIMEText(html_body, 'html'))
        
        pdf_bytes = local_generate_pdf(order, cart_snapshot)
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(pdf_bytes)
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f"attachment; filename=Facture_Atelier_{order.id}.pdf")
        msg.attach(part)
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_email, msg.as_string())
        server.quit()
        
        print(f"📧 [SMTP SUCCESS] Courriel envoyé personnellement à {recipient_email} !")
    except Exception as err:
        print(f"⚠️ [SMTP NATIVE ERROR] Échec : {str(err)}")
# backend/app/api/payments.py (Suite et fin du routeur transactionnel et logistique)

@router.post("/create-payment-intent")
async def create_and_confirm_payment_intent(
    payload: Request, 
    background_tasks: BackgroundTasks, 
    session: AsyncSession = Depends(get_async_session),
    current_user: Optional[User] = Depends(get_current_user)
):
    try:
        body = await payload.json()
        print(f"📥 Payload de caisse reçu : {body}")
        
        province_code = body.get("province_code")
        items = body.get("items", [])
        customer_name = body.get("fullName", "Client Anonyme")
        shipping_address = body.get("address", "Adresse de Livraison")
        city = body.get("city", "Ville")
        postal_code = body.get("postalCode", "H3B 1A7")
        customer_email = body.get("email", "fopsimella@gmail.com")

        if not items:
            raise HTTPException(status_code=400, detail="Le panier est vide")

        subtotal = 0.0
        cart_snapshot = []

        for item in items:
            product = await session.get(Product, item.get("product_id"))
            if not product or not product.is_active:
                raise HTTPException(status_code=404, detail="Produit introuvable")
            subtotal += product.price_cad * item.get("quantity", 1)
            
            cart_snapshot.append({
                "product_name": product.name,
                "price_snap": product.price_cad,
                "quantity": item.get("quantity", 1)
            })
            
        tax_summary = calculate_order_taxes(subtotal, province_code)
        amount_in_cents = int(round(tax_summary["total_with_tax"] * 100))
        
        items_metadata = [
            {"v_id": item.get("variant_id"), "qty": item.get("quantity")} for item in items
        ]
        
        intent = stripe.PaymentIntent.create(
            amount=amount_in_cents,
            currency="cad",
            payment_method_data={"type": "card", "card": {"token": "tok_visa"}},
            confirm=True,
            automatic_payment_methods={"enabled": True, "allow_redirects": "never"},
            metadata={
                "province_code": province_code,
                "subtotal": str(subtotal),
                "cart_items_json": json.dumps(items_metadata)
            }
        )
        
        if intent.status == "succeeded":
            new_order = Order(
                user_id=current_user.id if current_user else None,
                total_amount=tax_summary["total_with_tax"],
                tax_amount=tax_summary["tps_amount"] + tax_summary["tvp_amount"] + tax_summary["tvh_amount"],
                province_code=province_code,
                shipping_address=f"{customer_name}, {shipping_address}, {city}, {postal_code}, {customer_email}",
                status=OrderStatus.PAID,
                tracking_number=None
            )
            session.add(new_order)
            await session.flush()

            for item in items:
                product = await session.get(Product, item.get("product_id"))
                variant = await session.get(ProductVariant, item.get("variant_id"))
                quantity_bought = int(item.get("quantity", 1))
                
                if product and variant:
                    variant.stock = max(0, variant.stock - quantity_bought)
                    order_item = OrderItem(
                        order_id=new_order.id,
                        product_id=product.id,
                        variant_id=variant.id,
                        quantity=quantity_bought,
                        price_snap=product.price_cad
                    )
                    session.add(order_item)

            await session.commit()
            
            background_tasks.add_task(native_send_email, new_order, cart_snapshot, customer_email)
            print(f"💰 Commande enregistrée avec succès. ID: {new_order.id}. Facture routée vers : {customer_email}")
        
        return {"success": True, "status": intent.status, "total_to_pay_cad": tax_summary["total_with_tax"]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==========================================================================
# ✈️ ÉTAPE 3 : SYSTÈME DE SUIVI LOGISTIQUE ET EXTRACTION ADMINISTRATIVE
# ==========================================================================

@router.get("/admin/orders", response_model=List[Order])
async def list_all_orders_for_admin(
    session: AsyncSession = Depends(get_async_session),
    admin: User = Depends(get_current_admin)
):
    """
    Extrait l'intégralité des factures de commandes de la base pour l'onglet logistique.
    """
    statement = select(Order).order_by(Order.id.desc())
    results = await session.exec(statement)
    return results.all()


@router.post("/admin/orders/{order_id}/ship")
async def ship_order_and_notify_client(
    order_id: int,
    payload: Request,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_async_session),
    admin: User = Depends(get_current_admin)
):
    """
    Valide l'expédition : Associe le numéro Postes Canada, bascule le statut
    comptable sur SHIPPED et déclenche le mail de notification automatique à l'acheteur réel.
    """
    body = await payload.json()
    tracking_number = body.get("tracking_number")
    frontend_email = body.get("email")

    if not tracking_number:
        raise HTTPException(status_code=400, detail="Le numéro de suivi Postes Canada est requis.")

    order_result = await session.exec(select(Order).where(Order.id == order_id))
    db_order = order_result.one_or_none()

    if not db_order:
        raise HTTPException(status_code=404, detail="Cette facture de commande n'existe pas.")

    db_order.tracking_number = tracking_number
    db_order.status = OrderStatus.SHIPPED
    
    session.add(db_order)
    await session.commit()

    # 🕵️‍♂️ RECHERCHE EXTRA-SÉCURISÉE DE L'E-MAIL DE L'ACHETEUR (Vérification multiniveau)
    final_recipient = None

    # Niveau 1 : On lit l'e-mail envoyé par l'action du Dashboard React
    if frontend_email and "@" in frontend_email:
        final_recipient = frontend_email.strip()

    # Niveau 2 : Si vide, on extrait l'adresse e-mail imbriquée dans le champ shipping_address de l'acheteur
    if not final_recipient and db_order.shipping_address:
        segments = db_order.shipping_address.split(',')
        found_email_segment = next((s for s in segments if "@" in s), None)
        if found_email_segment:
            final_recipient = found_email_segment.strip()

    # Niveau 3 : Repli de sécurité ultime
    if not final_recipient:
        final_recipient = "fopsimella@gmail.com"

    background_tasks.add_task(send_shipping_email, db_order, final_recipient)
    print(f"✈️ Logistique validée. Colis #{order_id} scellé. Notification de suivi routée vers : {final_recipient}")
    return {"success": True, "detail": f"Commande marquée comme expédiée. Notification transmise à {final_recipient}"}


def send_shipping_email(order: Order, recipient_email: str):
    """
    Moteur SMTP d'expédition aux reflets canadiens.
    """
    try:
        sender_email = "fopsimella@gmail.com"
        sender_password = "bpvckgsoizztjobs"
        
        msg = MIMEMultipart()
        msg['From'] = f"L'Atelier Kamershoes <{sender_email}>"
        msg['To'] = recipient_email
        msg['Subject'] = f"✈️ Votre colis de l'Atelier est en route ! - Commande #ATK-00{order.id}"
        
        html_body = f"""
        <h3>Bonjour,</h3>
        <p>Les artisans de l'Atelier ont finalisé la confection de votre commande <b>ATK-00{order.id}</b>.</p>
        <p>Votre colis a été remis à <b>Postes Canada</b> et est officiellement en route vers votre adresse de livraison.</p>
        <div style="background-color: #faf9f6; padding: 15px; border-radius: 12px; border: 1px solid #f1f0ea; margin: 15px 0;">
            <p style="margin: 0; font-size: 13px; color: #1c1917;">🚚 <b>Numéro de suivi officiel :</b> <span style="font-family: monospace; color: #e02424; font-weight: bold;">{order.tracking_number}</span></p>
        </div>
        <p>Vous pouvez utiliser ce numéro directement sur le portail de Postes Canada pour suivre l'acheminement de vos souliers en temps réel.</p>
        <br/>
        <p>Merci pour votre confiance,<br/><b>L'Équipe Logistique de l'Atelier Canada</b> 🍁</p>
        """
        msg.attach(MIMEText(html_body, 'html'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_email, msg.as_string())
        server.quit()
        print(f"✈️ [LOGISTIQUE SUCCESS] Notification d'expédition acheminée à {recipient_email} !")
    except Exception as err:
        print(f"⚠️ [LOGISTIQUE ERROR] Échec : {str(err)}")

@router.post("/webhook", status_code=status.HTTP_200_OK)
async def stripe_webhook(request: Request):
    return {"status": "success"}

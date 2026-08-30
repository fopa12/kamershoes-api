# backend/app/core/invoice.py
import os
from io import BytesIO
from fpdf import FPDF
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from app.models.order import Order

# ⚙️ CONFIGURATION SMTP GMAIL DE PRODUCTION CERTIFIÉE
mail_config = ConnectionConfig(
    MAIL_USERNAME="fopsimella@gmail.com",              # ✅ Verified email transmission address
    MAIL_PASSWORD="bpvckgsoizztjobs",                  # 🔑 Google 16-character App Password
    MAIL_FROM="fopsimella@gmail.com",
    MAIL_FROM_NAME="L'Atelier Kamershoes Canada",
    MAIL_PORT=587,                                     # Standard TLS Google Port
    MAIL_SERVER="://gmail.com",                      # Google SMTP Route Gateway
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)


def generate_invoice_pdf(order: Order, cart_snapshot: list) -> bytes:
    """
    Génère un reçu PDF vectoriel, épuré et haut de gamme conforme aux exigences canadiennes.
    """
    pdf = FPDF()
    pdf.add_page()
    
    # En-tête de la marque de luxe
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "L'ATELIER KAMERSHOES CANADA", ln=True, align="C")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 5, "Confections Artisanales de Maroquinerie et Chaussures de Luxe", ln=True, align="C")
    pdf.cell(0, 5, "Support Client: support@kamershoes.ca | Bureau: Montreal, QC", ln=True, align="C")
    pdf.ln(10)
    
    # Ligne de séparation esthétique
    pdf.line(10, 38, 200, 35)
    pdf.ln(5)
    
    # Bloc d'informations : Commande & Livraison
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 7, f"RECU DE PAIEMENT # ATK-00{order.id}", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 5, f"Date de transaction : {order.created_at.strftime('%Y-%m-%d %H:%M') if order.created_at else 'Maintenant'}", ln=True)
    pdf.cell(0, 5, f"Statut comptable : PAYE (Autorise par Stripe)", ln=True)
    pdf.cell(0, 5, f"Adresse de livraison : {order.shipping_address} (Province: {order.province_code})", ln=True)
    pdf.ln(10)
    
    # En-tête du tableau de facturation
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(110, 7, "Description de la confection", border=1)
    pdf.cell(30, 7, "Prix Unitaire", border=1, align="C")
    pdf.cell(20, 7, "Quantite", border=1, align="C")
    pdf.cell(30, 7, "Total CAD", border=1, align="C")
    pdf.ln()
    
    # Read row variables directly from the safe dictionary snapshot passed from payments.py
    pdf.set_font("Helvetica", "", 10)
    if cart_snapshot:
        for entry in cart_snapshot:
            p_name = entry.get("product_name", "Article confection")
            p_snap = entry.get("price_snap", 0.0)
            p_qty = entry.get("quantity", 1)
            
            pdf.cell(110, 7, str(p_name), border=1)
            pdf.cell(30, 7, f"{p_snap:.2f} $", border=1, align="C")
            pdf.cell(20, 7, str(p_qty), border=1, align="C")
            pdf.cell(30, 7, f"{(p_snap * p_qty):.2f} $", border=1, align="C")
            pdf.ln()
    else:
        pdf.cell(110, 7, f"Commande de confections Atelier (Ref: Intent Stripe)", border=1)
        pdf.cell(30, 7, "- $", border=1, align="C")
        pdf.cell(20, 7, "1", border=1, align="C")
        pdf.cell(30, 7, f"{order.total_amount:.2f} $", border=1, align="C")
        pdf.ln()
        
    pdf.ln(5)
    
    # Calcul inverse des taxes pour l'affichage visuel sur le PDF
    pdf.set_font("Helvetica", "", 10)
    subtotal_recalc = order.total_amount - order.tax_amount
    pdf.cell(160, 6, "Sous-total :", align="R")
    pdf.cell(30, 6, f"{subtotal_recalc:.2f} $", align="C", ln=True)
    
    pdf.cell(160, 6, f"Taxes canadiennes collectees ({order.province_code}) :", align="R")
    pdf.cell(30, 6, f"{order.tax_amount:.2f} $", align="C", ln=True)
    
    # Ligne du Total Global absorbé
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(160, 8, "Montant Net Paye (CAD) :", align="R")
    pdf.cell(30, 8, f"{order.total_amount:.2f} $", border=1, align="C", ln=True)
    
    # Message de courtoisie de l'Atelier
    pdf.ln(12)
    pdf.set_font("Helvetica", "I", 9)
    pdf.cell(0, 5, "Chaque piece est confectionnee a la main. Un courriel vous sera envoye avec le numero de suivi des l'expedition.", align="C", ln=True)
    pdf.cell(0, 5, "Merci d'avoir choisi l'Atelier. Votre confiance est notre plus belle reussite.", align="C", ln=True)
    
    return pdf.output(dest='S')
# Continues directly below inside backend/app/core/invoice.py

async def send_invoice_email(order: Order, cart_snapshot: list, recipient_email: str):
    """
    ✅ 3-PARAMETER FIXED SIGNATURE: Accepts order metadata and flat snapshot data 
    directly, avoiding any data-unpacking or database query loop restrictions.
    """
    try:
        # Generate the high-utility vector PDF document straight from the payload list
        pdf_content = generate_invoice_pdf(order, cart_snapshot)
        
        # Build out the email markup presentation container layout
        customer_first_name = order.shipping_address.split(',')[0] if order.shipping_address else "Client"
        html_body = f"""
        <html>
            <body style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #1c1917; line-height: 1.6; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="border-bottom: 1px solid #e7e5e4; padding-bottom: 20px; margin-bottom: 20px;">
                    <h2 style="color: #b45309; font-weight: 300; letter-spacing: 1px; margin: 0;">L'ATELIER KAMERSHOES</h2>
                    <p style="font-size: 12px; color: #78716c; text-transform: uppercase; margin: 5px 0 0 0;">Confirmation de Commande & Reçu Officiel</p>
                </div>
                
                <p>Bonjour <b>{customer_first_name}</b>,</p>
                
                <p>Nous vous remercions pour votre commande à l'Atelier. Votre paiement par carte bancaire a été validé et sécurisé avec succès.</p>
                
                <div style="background-color: #f5f5f4; border-radius: 8px; padding: 15px; margin: 20px 0;">
                    <table style="width: 100%; font-size: 14px;">
                        <tr><td><b>Référence Facture :</b></td><td style="text-align: right;">ATK-00{order.id}</td></tr>
                        <tr><td><b>Montant Total :</b></td><td style="text-align: right; color: #b45309; font-weight: bold;">{order.total_amount:.2f} $ CAD</td></tr>
                        <tr><td><b>Destination :</b></td><td style="text-align: right;">{order.province_code} (Canada)</td></tr>
                        <tr><td><b>Statut de livraison :</b></td><td style="text-align: right; color: #15803d;">En préparation à l'Atelier</td></tr>
                    </table>
                </div>
                
                <p>Votre facture officielle détaillée ainsi que vos justificatifs fiscaux canadiens sont disponibles dans le document PDF joint à ce message.</p>
                
                <p style="font-size: 13px; color: #78716c; font-style: italic; margin-top: 30px;">
                    Nos artisans s'activent dès à présent sur vos confections. Vous recevrez un nouveau message contenant votre numéro de suivi Postes Canada dès le départ du colis.
                </p>
                
                <div style="border-top: 1px solid #e7e5e4; margin-top: 30px; padding-top: 20px; font-size: 11px; color: #a8a29e; text-align: center;">
                    L'Atelier Cameroun-Canada Inc. | Tous droits réservés.
                </div>
            </body>
        </html>
        """
        
        message = MessageSchema(
            subject=f"🧾 Votre reçu de paiement - Commande #ATK-00{order.id}",
            recipients=[recipient_email], 
            body=html_body,
            subtype=MessageType.html
        )
        
        # 📎 Securely attach memory PDF data bytes stream
        message.attachments.append({
            "file": pdf_content,
            "filename": f"Facture_Atelier_Kamershoes_{order.id}.pdf",
            "mime_type": "application/pdf"
        })
        
        fm = FastMail(mail_config)
        await fm.send_message(message)
        print(f"📧 [SMTP] Le courriel de facturation de la commande #{order.id} a été envoyé à {recipient_email}.")
        
    except Exception as email_err:
        print(f"⚠️ [SMTP Failure] Impossible d'expédier le mail : {str(email_err)}")

import g4f
from flask import render_template_string
from models import db, Email, Business
from datetime import datetime

# Configure g4f to use a reliable provider if possible, or just default
# It's better to keep it flexible as g4f providers change often.

def generate_gpt_email(business_name, business_address, website=None, pitch="website audit and optimization"):
    """
    Calls GPT4Free to generate a personalized email.
    """
    prompt = f"""
    Write a highly personalized, short, and professional cold outreach email to a local business.
    Business Name: {business_name}
    Location: {business_address}
    Website: {website or 'Not available'}
    Our Service Pitch: {pitch}
    
    Instructions:
    1. Mention the business name and acknowledge they are a local business.
    2. Be conversational, not salesy.
    3. Keep it under 150 words.
    4. Provide exactly two parts separated by a newline: 'Subject: [Your Subject]' and 'Body: [Your Body]'.
    """

    try:
        response = g4f.ChatCompletion.create(
            model=g4f.models.gpt_4,
            messages=[{"role": "user", "content": prompt}],
        )
        
        if response:
            # Simple parsing for Subject and Body
            lines = response.split('\n')
            subject = ""
            body = []
            
            for line in lines:
                if line.lower().startswith('subject:'):
                    subject = line.replace('Subject:', '').strip()
                elif line.strip():
                    # We skip the "Body:" header if it's there
                    clean_line = line.replace('Body:', '').strip()
                    if clean_line:
                        body.append(clean_line)
            
            if not subject:
                subject = f"Question for {business_name}"
                
            return subject, "\n\n".join(body)
            
    except Exception as e:
        print(f"GPT generation failed: {e}")
        return None, None

def write_email_content(email_id, app, pitch="website audit"):
    """
    Main entry point to populate an Email record with content.
    """
    with app.app_context():
        email_record = Email.query.get(email_id)
        if not email_record:
            return False
            
        business = email_record.business
        
        # 1. Try AI Generation
        subject, body = generate_gpt_email(business.name, business.address, business.website, pitch)
        
        # 2. Fallback to Jinja2 if AI failed
        if not subject or not body:
            print("Falling back to manual template...")
            with open('templates/email_template.txt', 'r') as f:
                template_content = f.read()
            
            # Simple manual parse of the fallback template
            lines = template_content.split('\n')
            subject_line = next((l for l in lines if l.startswith('Subject:')), f"Outreach for {business.name}")
            body_content = "\n".join(lines[1:])
            
            # Simple string replacement for basic personalization
            subject = subject_line.replace('Subject:', '').replace('{{ business_name }}', business.name).strip()
            body = body_content.replace('{{ business_name }}', business.name).strip()

        from config import Config
        from models import Setting
        
        # ... (AI generation and fallback logic here) ...
        # (Assuming subject and body are already populated above)
        
        # 3. Apply Global Signature replacement/append
        raw_sig = Setting.get('email_signature', Config.EMAIL_SIGNATURE)
        signature = raw_sig.replace('\\n', '\n') if raw_sig else ""
        
        # Clean up any generic placeholders the AI or template might have left
        body = body.replace('[Your Name]', '').replace('[Your Contact Information]', '').strip()
        
        # Append the new global signature
        if signature:
            body = f"{body}\n\n{signature}"

        # Update and save
        email_record.subject = subject
        email_record.email_body = body
        email_record.status = 'draft'
        email_record.generated_at = datetime.utcnow()
        
        db.session.commit()
        return True

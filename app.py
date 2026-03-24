from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Response
from config import Config
from models import db, Business, Email, SendLog
import os
import asyncio
from modules.scraper import scrape_google_maps, save_businesses

app = Flask(__name__)
app.config.from_object(Config)

# Initialize database
db.init_app(app)

with app.app_context():
    # Only creates tables if they don't exist
    db.create_all()
    print("Database and tables initialized.")

@app.route('/')
def index():
    """Dashboard / Scrape"""
    from datetime import date
    total_today = Business.query.filter(db.func.date(Business.scraped_at) == date.today()).count()
    return render_template('index.html', total_scraped_today=total_today)

@app.route('/scrape', methods=['POST'])
def scrape():
    """Trigger Scrape via AJAX/HTMX"""
    data = request.get_json(silent=True) or request.form or {}
    task_input = data.get('task_input', '').strip()
    
    # Fallback to older form data if accessed directly
    if not task_input:
        keyword = data.get('keyword')
        city = data.get('city')
        url_input = data.get('url')
        if url_input:
            task_input = url_input
        elif keyword and city:
            task_input = f"{keyword} in {city}"
    
    if not task_input:
        return f'<div class="p-6 bg-red-50 text-red-600 rounded-2xl border border-red-100 font-bold flex items-center"><i data-lucide="alert-circle" class="w-5 h-5 mr-3"></i> Error: Please provide a valid search query or Maps URL.</div>', 200

    if task_input.startswith('http') or task_input.startswith('www.'):
        maps_url = task_input
        query = None
    else:
        maps_url = None
        query = task_input
        
    try:
        # Run async scraper synchronously for the request
        scraped_data = asyncio.run(scrape_google_maps(search_query=query, url=maps_url, max_results=10))
        
        # Save results to DB (check duplicates by name+address)
        new_count = save_businesses(scraped_data, app)
        
        message = f"Successfully scraped {len(scraped_data)} businesses ({new_count} new entries)."
        return render_template('partials/scrape_results.html', businesses=scraped_data, message=message)
        
    except Exception as e:
        return f'<div class="p-6 bg-red-50 text-red-600 rounded-2xl border border-red-100 font-bold flex items-center"><i data-lucide="alert-circle" class="w-5 h-5 mr-3"></i> Error: {str(e)}</div>', 200

@app.route('/find-emails', methods=['POST'])
def find_emails():
    """Trigger Email Find via AJAX/HTMX"""
    from modules.email_finder import find_emails_for_business
    
    # Use get_json(silent=True) to avoid 415 errors
    data = request.get_json(silent=True) or request.form or {}
    business_id = data.get('business_id')
    
    if business_id:
        # Find for single business
        found = find_emails_for_business(business_id, app)
        if found:
            business = Business.query.get(business_id)
            business.has_email = True
            db.session.commit()
            return render_template('partials/business_row.html', b=business)
            
        business = Business.query.get(business_id)
        return render_template('partials/business_row.html', b=business)
    else:
        # Find for all businesses without email (limit to 10 for safety)
        tobefound = Business.query.filter_by(has_email=False).filter(Business.website != "").limit(10).all()
        total_found = 0
        for b in tobefound:
            found = find_emails_for_business(b.id, app)
            if found:
                b.has_email = True
                total_found += len(found)
        
        db.session.commit()
        return f'<div class="p-8 bg-indigo-50 text-indigo-700 rounded-3xl border border-indigo-100 font-bold text-center"><i data-lucide="search-check" class="w-10 h-10 mx-auto mb-4"></i> Scan Complete. Found {total_found} emails total across {len(tobefound)} sites. <a href="/businesses" class="block mt-4 text-xs underline">View businesses list</a></div>'

@app.route('/businesses')
def businesses():
    """Business List"""
    all_businesses = Business.query.order_by(Business.scraped_at.desc()).all()
    return render_template('businesses.html', businesses=all_businesses)

@app.route('/generate-email/<int:email_id>', methods=['POST'])
def generate_email(email_id):
    """Trigger AI Generation for a specific Email record"""
    from modules.ai_writer import write_email_content
    
    success = write_email_content(email_id, app)
    email_obj = Email.query.get(email_id)
    return render_template('partials/email_card.html', email=email_obj)

@app.route('/delete/<int:business_id>', methods=['DELETE', 'POST'])
def delete_business(business_id):
    b = Business.query.get(business_id)
    if b:
        Email.query.filter_by(business_id=b.id).delete()
        db.session.delete(b)
        db.session.commit()
    return ""

@app.route('/label/<int:business_id>', methods=['POST'])
def label_business(business_id):
    b = Business.query.get(business_id)
    if b:
        label = request.form.get('label')
        b.label = label
        db.session.commit()
    return render_template('businesses.html', businesses=Business.query.order_by(Business.scraped_at.desc()).all())

def generate_export_file(action, businesses):
    if action == 'export_csv':
        import csv
        from io import BytesIO, TextIOWrapper
        si = BytesIO()
        si.write(b'\xef\xbb\xbf') # UTF-8 BOM
        wrapper = TextIOWrapper(si, encoding='utf-8', newline='')
        cw = csv.writer(wrapper)
        cw.writerow(['ID', 'Name', 'Phone', 'Email', 'Website', 'Address', 'Rating', 'Label', 'Scraped At'])
        for b in businesses:
            emails = ", ".join([e.email for e in b.emails]) if b.emails else "N/A"
            cw.writerow([b.id, b.name, b.phone, emails, b.website, b.address, b.rating, b.label or '', b.scraped_at.strftime('%Y-%m-%d %H:%M') if b.scraped_at else ''])
        wrapper.flush()
        return Response(si.getvalue(), mimetype="text/csv", headers={"Content-disposition": "attachment; filename=leads_export.csv"})
    
    elif action == 'export_json':
        import json
        out = []
        for b in businesses:
            emails = [e.email for e in b.emails] if b.emails else []
            out.append({'id': b.id, 'name': b.name, 'phone': b.phone, 'emails': emails, 'website': b.website, 'address': b.address, 'rating': b.rating, 'label': b.label, 'scraped_at': b.scraped_at.strftime('%Y-%m-%d %H:%M') if b.scraped_at else None})
        return Response(json.dumps(out, indent=4), mimetype="application/json", headers={"Content-disposition": "attachment; filename=leads_export.json"})
    
    elif action == 'export_excel':
        import openpyxl
        from io import BytesIO
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Leads"
        ws.append(['ID', 'Name', 'Phone', 'Email', 'Website', 'Address', 'Rating', 'Label', 'Scraped At'])
        for b in businesses:
            emails = ", ".join([e.email for e in b.emails]) if b.emails else "N/A"
            ws.append([b.id, b.name, b.phone, emails, b.website, b.address, b.rating, b.label or '', b.scraped_at.strftime('%Y-%m-%d %H:%M') if b.scraped_at else ''])
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        return Response(output.getvalue(), mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-disposition": "attachment; filename=leads_export.xlsx"})
    
    elif action == 'export_pdf':
        from reportlab.lib.pagesizes import landscape, letter
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib import colors
        from io import BytesIO
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
        elements = []
        styles = getSampleStyleSheet()
        styleN = styles["Normal"]
        data = [['Name', 'Phone', 'Email', 'Website', 'Label']]
        for b in businesses:
            emails = ", ".join([e.email for e in b.emails]) if b.emails else "N/A"
            data.append([Paragraph(b.name or '', styleN), b.phone or 'N/A', Paragraph(emails, styleN), Paragraph(b.website or 'N/A', styleN), b.label or 'None'])
        t = Table(data, colWidths=[180, 100, 150, 150, 80])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2563eb')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e5e7eb')),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        elements.append(t)
        doc.build(elements)
        buffer.seek(0)
        return Response(buffer.getvalue(), mimetype="application/pdf", headers={"Content-disposition": "attachment; filename=leads_export.pdf"})
        
    return redirect(url_for('businesses'))

@app.route('/export/<format_type>')
def export_general(format_type):
    # Route for the global header export buttons (Exports all)
    businesses = Business.query.order_by(Business.scraped_at.desc()).all()
    action = f'export_{format_type}'
    return generate_export_file(action, businesses)

@app.route('/bulk-action', methods=['POST'])
def bulk_action():
    action = request.form.get('action')
    selected_ids = request.form.getlist('selected_ids')
    
    if action and action.startswith('export_') and not selected_ids:
        # Fallback to export all if attempted via dropdown with no selections
        businesses = Business.query.order_by(Business.scraped_at.desc()).all()
    else:
        businesses = Business.query.filter(Business.id.in_(selected_ids)).order_by(Business.scraped_at.desc()).all() if selected_ids else []
    
    if action and action.startswith('export_'):
        return generate_export_file(action, businesses)
        
    if action == 'delete':
        if not selected_ids: return redirect(url_for('businesses'))
        for b in businesses:
            Email.query.filter_by(business_id=b.id).delete()
            db.session.delete(b)
        db.session.commit()
    elif action == 'label':
        if not selected_ids: return redirect(url_for('businesses'))
        new_label = request.form.get('bulk_label')
        for b in businesses:
            b.label = new_label
        db.session.commit()
        
    return redirect(url_for('businesses'))

@app.route('/preview')
def preview():
    """Email Preview & Approval"""
    # Fetch emails with some content or those that need content
    draft_emails = Email.query.order_by(Email.id.desc()).all()
    return render_template('preview.html', emails=draft_emails)

@app.route('/send/<int:email_id>', methods=['POST'])
def send_email(email_id):
    """Trigger sending for a single Email record"""
    from modules.mailer import send_outreach_email
    
    data = request.get_json(silent=True) or request.form or {}
    dry_run = data.get('dry_run', Config.DRY_RUN)
    
    msg, success = send_outreach_email(email_id, app, dry_run=dry_run)
    email_obj = Email.query.get(email_id)
    return render_template('partials/email_card.html', email=email_obj, send_msg=msg)

@app.route('/send-all', methods=['POST'])
def send_all():
    """Trigger sending for all approved/ready emails"""
    from modules.mailer import send_all_approved
    
    dry_run = request.json.get('dry_run', Config.DRY_RUN) if request.json else Config.DRY_RUN
    
    count = send_all_approved(app, dry_run=dry_run)
    
    return jsonify({
        "status": "success",
        "message": f"Successfully processed {count} emails."
    })

@app.route('/logs')
def logs():
    """Send Log History"""
    from datetime import date
    all_logs = SendLog.query.order_by(SendLog.sent_at.desc()).all()
    sent_today = SendLog.query.filter(db.func.date(SendLog.sent_at) == date.today(), SendLog.status == 'sent').count()
    return render_template('logs.html', logs=all_logs, sent_today=sent_today, daily_limit=Config.DAILY_EMAIL_LIMIT)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    """Global System Settings"""
    from models import Setting
    
    if request.method == 'POST':
        new_signature = request.form.get('signature')
        Setting.set('email_signature', new_signature)
        flash('Settings saved successfully.', 'success')
        return redirect(url_for('settings'))
        
    current_signature = Setting.get('email_signature', Config.EMAIL_SIGNATURE)
    # Format the signature correctly for textarea display (replace \n from .env if needed, though standard \n is fine)
    if current_signature and '\\n' in current_signature:
        current_signature = current_signature.replace('\\n', '\n')
        
    return render_template('settings.html', signature=current_signature)

if __name__ == '__main__':
    app.run(debug=True, port=5000)

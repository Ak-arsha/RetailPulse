"""Generate Akarsha_Agarwal_Resume.pdf with reportlab preserving all formatting and hyperlinks."""
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable

def generate_pdf(filename="Akarsha_Agarwal_Resume.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=28,
        bottomMargin=28
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'HeaderTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=22,
        alignment=1, # Center
        textColor=colors.HexColor('#000000')
    )

    header_contacts = ParagraphStyle(
        'HeaderContacts',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        alignment=1, # Center
        textColor=colors.HexColor('#1F2937')
    )

    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#000000'),
        spaceBefore=6,
        spaceAfter=2
    )

    normal_body = ParagraphStyle(
        'NormalBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#111827')
    )

    bullet_body = ParagraphStyle(
        'BulletBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        leftIndent=12,
        spaceAfter=2,
        textColor=colors.HexColor('#1F2937')
    )

    table_header = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=10,
        textColor=colors.HexColor('#000000')
    )

    table_cell = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=10,
        textColor=colors.HexColor('#111827')
    )

    elements = []

    # 1. HEADER
    elements.append(Paragraph("AKARSHA AGARWAL", title_style))
    elements.append(Spacer(1, 3))
    
    contacts_html = (
        'Phone: <a href="tel:+916387671250" color="#0044CC">+91 6387671250</a> &nbsp;|&nbsp; '
        'Email: <a href="mailto:akarshaagarwal25@gmail.com" color="#0044CC">akarshaagarwal25@gmail.com</a> &nbsp;|&nbsp; '
        'LinkedIn: <a href="https://linkedin.com/in/akarsha-agarwal" color="#0044CC">Akarsha Agarwal</a> &nbsp;|&nbsp; '
        'GitHub: <a href="https://github.com/Ak-arsha" color="#0044CC">Ak-arsha</a>'
    )
    elements.append(Paragraph(contacts_html, header_contacts))
    elements.append(Spacer(1, 4))

    def add_section_header(title):
        elements.append(Paragraph(f"<b>{title}</b>", section_heading))
        elements.append(HRFlowable(width="100%", thickness=0.75, color=colors.HexColor("#000000"), spaceBefore=1, spaceAfter=4))

    # 2. EDUCATION
    add_section_header("EDUCATION")
    edu_data = [
        [Paragraph("<b>Year</b>", table_header), Paragraph("<b>Degree / Certificate</b>", table_header), Paragraph("<b>Institute</b>", table_header), Paragraph("<b>CGPA / %</b>", table_header)],
        [Paragraph("2023 – 2027", table_cell), Paragraph("B.Tech, Computer Science & Engineering", table_cell), Paragraph("Jaypee Institute of Information Technology, Noida", table_cell), Paragraph("7.17 / 10.0", table_cell)],
        [Paragraph("2022 – 2023", table_cell), Paragraph("Class XII, CMS Rajendra Nagar 1", table_cell), Paragraph("Lucknow, Uttar Pradesh", table_cell), Paragraph("94.75%", table_cell)],
        [Paragraph("2021 – 2022", table_cell), Paragraph("Class X, CMS Rajendra Nagar 1", table_cell), Paragraph("Lucknow, Uttar Pradesh", table_cell), Paragraph("93.8%", table_cell)],
    ]
    edu_table = Table(edu_data, colWidths=[70, 210, 180, 80])
    edu_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#9CA3AF")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(edu_table)
    elements.append(Spacer(1, 4))

    # 3. EXPERIENCE
    add_section_header("EXPERIENCE")
    
    # Eglogics
    exp1_title = '<b>Python Developer</b> | <a href="https://eglogics.com/" color="#0044CC"><u>Eglogics Softech Pvt. Ltd.</u></a>'
    exp1_date = '<i>Mar 2026 – Apr 2026</i>'
    exp1_table = Table([[Paragraph(exp1_title, normal_body), Paragraph(exp1_date, ParagraphStyle('R', parent=normal_body, alignment=2))]], colWidths=[400, 140])
    exp1_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('LEFTPADDING', (0,0), (-1,-1), 0), ('RIGHTPADDING', (0,0), (-1,-1), 0)]))
    elements.append(exp1_table)
    elements.append(Spacer(1, 2))
    elements.append(Paragraph("&bull; Built an automated face-recognition attendance system in Python and OpenCV that identifies individuals via facial features and records attendance digitally, replacing manual tracking.", bullet_body))
    elements.append(Paragraph("&bull; Integrated facial recognition with a Flask backend and SQL database, enabling faster, contactless attendance capture and reducing administrative workload and recording errors.", bullet_body))
    elements.append(Spacer(1, 4))

    # IIT BHU
    exp2_title = '<b>Research Intern</b> | <a href="https://iitbhu.ac.in/" color="#0044CC"><u>IIT (BHU) Varanasi</u></a>'
    exp2_date = '<i>May 2026 – Jul 2026</i>'
    exp2_table = Table([[Paragraph(exp2_title, normal_body), Paragraph(exp2_date, ParagraphStyle('R', parent=normal_body, alignment=2))]], colWidths=[400, 140])
    exp2_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('LEFTPADDING', (0,0), (-1,-1), 0), ('RIGHTPADDING', (0,0), (-1,-1), 0)]))
    elements.append(exp2_table)
    elements.append(Spacer(1, 2))
    elements.append(Paragraph("&bull; Developed PaddyCare AI, a deep learning system to classify 10 major paddy crop diseases plus healthy leaves from images, using YOLO and EfficientNet with transfer learning, data augmentation, and fine-tuning.", bullet_body))
    elements.append(Paragraph("&bull; Built and deployed an inference pipeline with FastAPI and Streamlit to support early disease detection for farmers, aiding faster intervention and reduced crop loss.", bullet_body))
    elements.append(Spacer(1, 4))

    # 4. TECHNICAL SKILLS
    add_section_header("TECHNICAL SKILLS")
    skills_text = (
        '<b>Languages:</b> C, C++, Python, Java, SQL, JavaScript, PHP<br/>'
        '<b>Data Engineering & Cloud:</b> PySpark, SQL (PostgreSQL, SQLite), dbt, SQLAlchemy, Pandera, Docker, AWS (S3, EC2, ECR), Dagster, REST APIs, Git/GitHub<br/>'
        '<b>ML / DL & CV:</b> PyTorch, TensorFlow, OpenCV, Scikit-learn, XGBoost, LightGBM, MediaPipe, YOLO, EfficientNet, spaCy, Transformers<br/>'
        '<b>Web & Frameworks:</b> FastAPI, Streamlit, Plotly, Flask, Django, Django REST Framework, React.js, Node.js, WebRTC<br/>'
        '<b>Databases & Tools:</b> PostgreSQL, Supabase, SQLite, Jupyter Notebook, VS Code, Google Colab<br/>'
        '<b>Competitive Programming:</b> 1388 rating on Codeforces (<a href="https://codeforces.com/profile/Akarsha__Agarwal" color="#0044CC">Akarsha__Agarwal</a>) &middot; '
        '300+ problems on LeetCode (<a href="https://leetcode.com/u/Akarsha11" color="#0044CC">Akarsha11</a>) &middot; '
        '360+ problems on TUF+ (<a href="https://takeuforward.org/" color="#0044CC">Akarsha</a>)'
    )
    elements.append(Paragraph(skills_text, normal_body))
    elements.append(Spacer(1, 4))

    # 5. PROJECTS
    add_section_header("PROJECTS")
    
    # DataPulse (NEW PROJECT)
    p1_title = '<b>DataPulse – Enterprise Multi-Industry Data Platform</b> (<a href="https://retailpulse-kusoong2ux9ifqhtrhrznb.streamlit.app/" color="#0044CC">Live Demo</a> | <a href="https://github.com/Ak-arsha/RetailPulse" color="#0044CC">GitHub</a>)'
    p1_tech = '<i>Python, SQL, PySpark, FastAPI, PostgreSQL, Pandera, dbt, Streamlit, Plotly, Docker, AWS, Gemini API, Dagster</i>'
    elements.append(Paragraph(f"{p1_title}<br/>{p1_tech}", normal_body))
    elements.append(Spacer(1, 2))
    elements.append(Paragraph("&bull; Architected an automated multi-domain ETL data engineering pipeline ingesting 25K+ raw records across Retail, SaaS, Healthcare, and Hi-Tech verticals with Pandera DLQ validation and a 100% row-count reconciliation assertion (<i>Raw = Clean + Quarantine + Duplicates</i>).", bullet_body))
    elements.append(Paragraph("&bull; Modeled a PostgreSQL Star Schema database with CTEs, Window Functions (<i>NTILE</i>), Slowly Changing Dimensions (SCD2), and dbt marts (<i>v_customer_rfm</i>, <i>v_saas_metrics</i>, <i>v_healthcare_sla</i>, <i>v_hitech_telemetry</i>) to power executive dashboards.", bullet_body))
    elements.append(Paragraph("&bull; Developed a multi-tenant Streamlit + Plotly interactive dashboard with JWT auth/RBAC (Admin, Analyst, Viewer), server-enforced PII masking for healthcare data, and a Google Gemini Text-to-SQL assistant backed by a secured FastAPI REST API.", bullet_body))
    elements.append(Spacer(1, 4))

    # Picture Perfect
    p2_title = '<b>Picture Perfect – AI-Powered Image Editing Studio</b> (<a href="https://github.com/Ak-arsha/Picture-Perfect" color="#0044CC">Link</a>)'
    p2_tech = '<i>Python, Streamlit, OpenCV, MediaPipe, Gemini API, Supabase</i>'
    elements.append(Paragraph(f"{p2_title}<br/>{p2_tech}", normal_body))
    elements.append(Spacer(1, 2))
    elements.append(Paragraph("&bull; Built an interactive web studio for real-time image editing with automated smile enhancement and gaze correction using MediaPipe Face Mesh, plus natural-language photo editing powered by the Gemini API.", bullet_body))
    elements.append(Spacer(1, 4))

    # KrishiMitra
    p3_title = '<b>KrishiMitra – AI Farm Advisory Platform</b> (<a href="https://github.com/Ak-arsha/KrishiMitra" color="#0044CC">Link</a>)'
    p3_tech = '<i>Next.js, FastAPI, XGBoost, LightGBM, Supabase</i>'
    elements.append(Paragraph(f"{p3_title}<br/>{p3_tech}", normal_body))
    elements.append(Spacer(1, 2))
    elements.append(Paragraph("&bull; Built a full-stack advisory platform for farmers with ML-based 5-day crop price forecasting, an explainable-AI panel, and a geo-spatial buyer recommendation engine using the haversine formula.", bullet_body))
    elements.append(Paragraph("&bull; Designed a sell/store decision engine comparing live market prices to government MSP floors, with JWT/Google OAuth authentication and a FastAPI + PostgreSQL (Supabase) backend.", bullet_body))
    elements.append(Spacer(1, 4))

    # 6. PUBLICATIONS
    add_section_header("PUBLICATIONS")
    pub_title = '<b>LocalMark: Robust Localised Message Watermarking for Secure Digital Image Copyright Protection</b> — <i>Under review, Journal of the Franklin Institute (2026)</i>'
    elements.append(Paragraph(pub_title, normal_body))
    elements.append(Spacer(1, 2))
    elements.append(Paragraph("&bull; Co-authored a U-Net-based watermarking framework for embedding patient-identifying messages into medical retinal images; contributed to data curation and manuscript drafting. Proposed Enhanced Robust Decoder achieved 96% bit accuracy and 48.27 dB PSNR across 24 real-world image attacks, outperforming four baseline architectures.", bullet_body))
    elements.append(Spacer(1, 4))

    # 7. ACHIEVEMENTS
    add_section_header("ACHIEVEMENTS")
    elements.append(Paragraph("&bull; Selected for the presentation round of Smart India Hackathon 2024 for a solution built around the “Root of Trust” problem statement.", bullet_body))
    elements.append(Paragraph("&bull; Selected as Team Lead of the AI/ML Domain under GDG (Google Developers Group), Jaypee Institute of Information Technology.", bullet_body))

    doc.build(elements)
    print(f"[PDF Export Success] Generated {filename}")

if __name__ == "__main__":
    generate_pdf()

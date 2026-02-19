"""
Export service for resume data.

This module provides functionality to export parsed resume data in various formats:
- PDF generation using reportlab
- WhatsApp share link generation
- Telegram share link generation
- Email mailto link generation
"""

from io import BytesIO
from typing import Dict, List, Optional
from urllib.parse import quote, urlencode

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table


# Default application base URL for generating share links
DEFAULT_BASE_URL = "http://localhost:3000"


def format_resume_text(resume_data: Dict) -> str:
    """
    Format resume data as plain text.

    This formats the resume data into a readable text representation
    suitable for sharing via messaging apps or email.

    Args:
        resume_data: Parsed resume data dictionary

    Returns:
        Formatted resume as text string
    """
    lines = []

    # Personal Information
    personal_info = resume_data.get("personal_info", {})
    if personal_info:
        name = personal_info.get("full_name", "Unknown")
        lines.append(f"RESUME: {name}")
        lines.append("=" * 50)

        if personal_info.get("email"):
            lines.append(f"Email: {personal_info['email']}")
        if personal_info.get("phone"):
            lines.append(f"Phone: {personal_info['phone']}")
        if personal_info.get("location"):
            lines.append(f"Location: {personal_info['location']}")
        lines.append("")

    # Work Experience
    work_experience = resume_data.get("work_experience", [])
    if work_experience:
        lines.append("WORK EXPERIENCE")
        lines.append("-" * 50)
        for exp in work_experience:
            title = exp.get("title", "Position")
            company = exp.get("company", "Company")
            start = exp.get("start_date", "")
            end = exp.get("end_date", "")
            lines.append(f"{title} at {company}")
            if start or end:
                lines.append(f"  {start} - {end}")
            description = exp.get("description", "")
            if description:
                lines.append(f"  {description}")
            lines.append("")

    # Education
    education = resume_data.get("education", [])
    if education:
        lines.append("EDUCATION")
        lines.append("-" * 50)
        for edu in education:
            institution = edu.get("institution", "Institution")
            degree = edu.get("degree", "Degree")
            lines.append(f"{degree}")
            lines.append(f"  {institution}")
            gpa = edu.get("gpa", "")
            if gpa:
                lines.append(f"  GPA: {gpa}")
            lines.append("")

    # Skills
    skills = resume_data.get("skills", {})
    if skills:
        lines.append("SKILLS")
        lines.append("-" * 50)
        for skill_type, skill_list in skills.items():
            if skill_list and isinstance(skill_list, list):
                skill_type_label = skill_type.replace("_", " ").title()
                lines.append(f"{skill_type_label}: {', '.join(skill_list)}")
        lines.append("")

    return "\n".join(lines)


def generate_pdf(resume_data: Dict) -> bytes:
    """
    Generate a PDF file from resume data.

    Creates a professional-looking PDF document with formatted resume content
    including personal information, work experience, education, and skills.

    Args:
        resume_data: Parsed resume data dictionary

    Returns:
        PDF file content as bytes
    """
    buffer = BytesIO()

    # Create PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch
    )

    # Container for PDF elements
    elements = []

    # Custom styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor='#2C3E50',
        spaceAfter=12,
        fontName='Helvetica-Bold'
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor='#34495E',
        spaceAfter=6,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        textColor='#2C3E50',
        spaceAfter=6,
        fontName='Helvetica'
    )
    small_style = ParagraphStyle(
        'CustomSmall',
        parent=styles['Normal'],
        fontSize=9,
        textColor='#7F8C8D',
        spaceAfter=3,
        fontName='Helvetica'
    )

    # Personal Information
    personal_info = resume_data.get("personal_info", {})
    if personal_info:
        name = personal_info.get("full_name", "Unknown")
        elements.append(Paragraph(name, title_style))
        elements.append(Spacer(1, 0.1 * inch))

        # Contact info table
        contact_data = []
        if personal_info.get("email"):
            contact_data.append([Paragraph("<b>Email:</b>", normal_style), Paragraph(personal_info["email"], normal_style)])
        if personal_info.get("phone"):
            contact_data.append([Paragraph("<b>Phone:</b>", normal_style), Paragraph(personal_info["phone"], normal_style)])
        if personal_info.get("location"):
            contact_data.append([Paragraph("<b>Location:</b>", normal_style), Paragraph(personal_info["location"], normal_style)])

        if contact_data:
            contact_table = Table(contact_data, colWidths=[1.2 * inch, 4 * inch])
            contact_table.setStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ])
            elements.append(contact_table)

        elements.append(Spacer(1, 0.2 * inch))

    # Work Experience
    work_experience = resume_data.get("work_experience", [])
    if work_experience:
        elements.append(Paragraph("Work Experience", heading_style))
        elements.append(Spacer(1, 0.1 * inch))

        for exp in work_experience:
            title = exp.get("title", "Position")
            company = exp.get("company", "Company")
            start = exp.get("start_date", "")
            end = exp.get("end_date", "")

            # Title and company
            elements.append(Paragraph(f"<b>{title}</b> at {company}", normal_style))

            # Date range
            if start or end:
                date_range = f"{start} - {end}" if start else end
                elements.append(Paragraph(date_range, small_style))

            # Description
            description = exp.get("description", "")
            if description:
                # Convert newlines to <br/> for HTML-like formatting in PDF
                formatted_desc = description.replace('\n', '<br/>')
                elements.append(Paragraph(formatted_desc, normal_style))

            elements.append(Spacer(1, 0.1 * inch))

    # Education
    education = resume_data.get("education", [])
    if education:
        elements.append(Paragraph("Education", heading_style))
        elements.append(Spacer(1, 0.1 * inch))

        for edu in education:
            institution = edu.get("institution", "Institution")
            degree = edu.get("degree", "Degree")
            gpa = edu.get("gpa", "")

            elements.append(Paragraph(f"<b>{degree}</b>", normal_style))
            elements.append(Paragraph(institution, normal_style))

            if gpa:
                elements.append(Paragraph(f"GPA: {gpa}", small_style))

            elements.append(Spacer(1, 0.1 * inch))

    # Skills
    skills = resume_data.get("skills", {})
    if skills:
        elements.append(Paragraph("Skills", heading_style))
        elements.append(Spacer(1, 0.1 * inch))

        for skill_type, skill_list in skills.items():
            if skill_list and isinstance(skill_list, list):
                skill_type_label = skill_type.replace("_", " ").title()
                skills_text = f"<b>{skill_type_label}:</b> {', '.join(skill_list)}"
                elements.append(Paragraph(skills_text, normal_style))

    # Build PDF
    doc.build(elements)

    # Get PDF bytes
    pdf_bytes = buffer.getvalue()
    buffer.close()

    return pdf_bytes


def generate_whatsapp_link(resume_data: Dict, base_url: str = DEFAULT_BASE_URL) -> str:
    """
    Generate a WhatsApp share link for a resume.

    Creates a WhatsApp URL that pre-fills a message with a link to the shared resume.

    Args:
        resume_data: Parsed resume data dictionary
        base_url: Base URL for the application (used for constructing share links)

    Returns:
        WhatsApp share URL (wa.me format)
    """
    # Format resume as text
    resume_text = format_resume_text(resume_data)

    # Create a concise message
    personal_info = resume_data.get("personal_info", {})
    name = personal_info.get("full_name", "A candidate")
    message = f"Check out {name}'s resume:\n\n{resume_text}"

    # URL encode the message
    encoded_message = quote(message)

    # Return WhatsApp URL
    return f"https://wa.me/?text={encoded_message}"


def generate_telegram_link(resume_data: Dict, base_url: str = DEFAULT_BASE_URL) -> str:
    """
    Generate a Telegram share link for a resume.

    Creates a Telegram URL that pre-fills a message with a link to the shared resume.

    Args:
        resume_data: Parsed resume data dictionary
        base_url: Base URL for the application (used for constructing share links)

    Returns:
        Telegram share URL (t.me format)
    """
    # Format resume as text
    resume_text = format_resume_text(resume_data)

    # Create a concise message
    personal_info = resume_data.get("personal_info", {})
    name = personal_info.get("full_name", "A candidate")
    message = f"Check out {name}'s resume:\n\n{resume_text}"

    # URL encode the message
    encoded_message = quote(message)

    # Return Telegram URL
    return f"https://t.me/share/url?url=&text={encoded_message}"


def generate_email_link(resume_data: Dict, base_url: str = DEFAULT_BASE_URL) -> str:
    """
    Generate an email mailto link for sharing a resume.

    Creates a mailto URL that pre-fills the subject and body with resume information.

    Args:
        resume_data: Parsed resume data dictionary
        base_url: Base URL for the application (used for constructing share links)

    Returns:
        Email mailto URL
    """
    # Format resume as text
    resume_text = format_resume_text(resume_data)

    # Create subject and body
    personal_info = resume_data.get("personal_info", {})
    name = personal_info.get("full_name", "A Candidate")

    subject = f"Resume: {name}"
    body = f"Please find the resume details below:\n\n{resume_text}"

    # URL encode subject and body
    encoded_subject = quote(subject)
    encoded_body = quote(body)

    # Return mailto URL
    return f"mailto:?subject={encoded_subject}&body={encoded_body}"

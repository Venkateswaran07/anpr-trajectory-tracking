import os
import re
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Preformatted
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def markdown_to_pdf(md_path, pdf_path):
    with open(md_path, 'r', encoding='utf-8') as f:
        text = f.read()

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Title'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#1e293b'),
        alignment=0,
        spaceAfter=12
    )

    h1_style = ParagraphStyle(
        'H1',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=17,
        textColor=colors.HexColor('#0f172a'),
        spaceBefore=12,
        spaceAfter=6
    )

    h2_style = ParagraphStyle(
        'H2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#2563eb'),
        spaceBefore=8,
        spaceAfter=4
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12.5,
        textColor=colors.HexColor('#334155'),
        spaceAfter=5
    )

    code_style = ParagraphStyle(
        'Code',
        fontName='Courier',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor('#0f172a'),
        backColor=colors.HexColor('#f8fafc'),
        borderColor=colors.HexColor('#cbd5e1'),
        borderWidth=0.5,
        borderPadding=5,
        spaceBefore=5,
        spaceAfter=5
    )

    story = []
    lines = text.split('\n')
    in_code = False
    code_block = []

    for line in lines:
        if line.startswith('```'):
            if in_code:
                code_text = '\n'.join(code_block)
                story.append(Preformatted(code_text, code_style))
                code_block = []
                in_code = False
            else:
                in_code = True
            continue

        if in_code:
            code_block.append(line)
            continue

        if not line.strip():
            story.append(Spacer(1, 3))
            continue

        if line.startswith('# '):
            story.append(Paragraph(line[2:].strip(), title_style))
            story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e2e8f0'), spaceAfter=8))
        elif line.startswith('## '):
            story.append(Paragraph(line[3:].strip(), h1_style))
        elif line.startswith('### '):
            story.append(Paragraph(line[4:].strip(), h2_style))
        elif line.startswith('---'):
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#cbd5e1'), spaceBefore=6, spaceAfter=6))
        else:
            formatted_line = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
            formatted_line = re.sub(r'\*(.*?)\*', r'<i>\1</i>', formatted_line)
            story.append(Paragraph(formatted_line, body_style))

    doc.build(story)
    print(f"[SUCCESS] Updated PDF Generated at: {pdf_path}")

if __name__ == '__main__':
    md_file = r'C:\Users\Lenovo\.gemini\antigravity\brain\e7e2c150-7fea-4622-ba51-161f928a97ce\artifacts\Vehicle_Surveillance_Technical_Presentation_Guide.md'
    pdf_file = r'd:\downloads\Vehicle_Surveillance\Vehicle_Surveillance_Technical_Presentation_Guide.pdf'
    markdown_to_pdf(md_file, pdf_file)

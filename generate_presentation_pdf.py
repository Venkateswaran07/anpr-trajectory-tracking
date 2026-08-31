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

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Title'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#1e293b'),
        alignment=0,
        spaceAfter=15
    )

    h1_style = ParagraphStyle(
        'H1',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=18,
        textColor=colors.HexColor('#0f172a'),
        spaceBefore=14,
        spaceAfter=8
    )

    h2_style = ParagraphStyle(
        'H2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=colors.HexColor('#2563eb'),
        spaceBefore=10,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor('#334155'),
        spaceAfter=6
    )

    code_style = ParagraphStyle(
        'Code',
        fontName='Courier',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#0f172a'),
        backColor=colors.HexColor('#f1f5f9'),
        borderColor=colors.HexColor('#cbd5e1'),
        borderWidth=0.5,
        borderPadding=6,
        spaceBefore=6,
        spaceAfter=6
    )

    story = []
    lines = text.split('\n')
    in_code = False
    code_block = []

    for line in lines:
        if line.startswith('```'):
            if in_code:
                # End code block
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
            story.append(Spacer(1, 4))
            continue

        if line.startswith('# '):
            story.append(Paragraph(line[2:].strip(), title_style))
            story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e2e8f0'), spaceAfter=10))
        elif line.startswith('## '):
            story.append(Paragraph(line[3:].strip(), h1_style))
        elif line.startswith('### '):
            story.append(Paragraph(line[4:].strip(), h2_style))
        elif line.startswith('---'):
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#cbd5e1'), spaceBefore=8, spaceAfter=8))
        else:
            # Inline formatting
            formatted_line = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
            formatted_line = re.sub(r'\*(.*?)\*', r'<i>\1</i>', formatted_line)
            story.append(Paragraph(formatted_line, body_style))

    doc.build(story)
    print(f"[SUCCESS] PDF Generated at: {pdf_path}")

if __name__ == '__main__':
    md_file = r'C:\Users\Lenovo\.gemini\antigravity\brain\e7e2c150-7fea-4622-ba51-161f928a97ce\artifacts\Vehicle_Surveillance_Technical_Presentation_Guide.md'
    pdf_file = r'd:\downloads\Vehicle_Surveillance\Vehicle_Surveillance_Technical_Presentation_Guide.pdf'
    markdown_to_pdf(md_file, pdf_file)

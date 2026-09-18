import os
import sys
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable

def generate_pdf(output_path="docs/TraceX_Project_Report.pdf"):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=45,
        leftMargin=45,
        topMargin=45,
        bottomMargin=45
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=colors.HexColor('#0b2545'),
        alignment=1, # Center
        spaceAfter=10
    )
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#0066cc'),
        alignment=1,
        spaceAfter=25
    )
    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#0b2545'),
        spaceBefore=14,
        spaceAfter=6
    )
    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor('#223344'),
        spaceBefore=8,
        spaceAfter=4
    )
    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=6
    )
    bullet_style = ParagraphStyle(
        'BulletText',
        parent=body_style,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=3
    )
    code_style = ParagraphStyle(
        'CodeStyle',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#004488'),
        spaceAfter=4
    )

    elements = []

    # Title Banner
    elements.append(Paragraph("TraceX — Digital Incident Investigation &amp; Evidence Management System", title_style))
    elements.append(Paragraph("From Evidence to Timeline — A Transparent Forensic Investigation Workspace", subtitle_style))
    elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#0066cc'), spaceAfter=15))

    # Meta Table
    meta_data = [
        ["Course / Track:", "Cyber Forensics & Incident Response (CSE Specialization)", "Date:", "September 2026"],
        ["Framework:", "Python 3.13 / Flask 3.1 / SQLite (3NF)", "Verification:", "10/10 Automated Tests Passed"],
        ["Architecture:", "Strict 3-Tier Layered Design", "Status:", "Approved Blueprint v1.0.0 Frozen"]
    ]
    meta_table = Table(meta_data, colWidths=[110, 200, 70, 140])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f0f4f8')),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor('#1f2937')),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME', (2,0), (2,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#d0d7de'))
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 15))

    # Sections
    sections = [
        ("1. Executive Summary & Problem Statement",
         "TraceX resolves a fundamental limitation in digital forensics education: the divide between static, non-functional UI mockups and proprietary enterprise platforms (EnCase, FTK) that are inaccessible for rapid academic evaluation. TraceX provides a fully auditable, local DFIR workspace that models real-world forensic imperatives—verifiable SHA-256 integrity, append-only custody trails, deterministic rule engines, and O(n log n) timeline sorting—strictly using safe synthetic data."),

        ("2. Architecture & Layer Separation",
         "The system strictly enforces a 3-tier layered design: Browser (HTML/CSS/JS + Chart.js) -> Controller Blueprints -> RBAC Middleware (@role_required) -> Service Layer -> Repository Layer -> SQLite (PRAGMA foreign_keys = ON) + isolated evidence store. No route queries the database directly; every data interaction is encapsulated in parameterized repository queries."),

        ("3. Database Design & 3NF Normalization",
         "The database contains exactly six approved entities in Third Normal Form (3NF): User, Case, Evidence, CustodyRecord, SecurityEvent, and Finding. Composite and foreign key indexes optimize chronological sorting and case filtering. CustodyRecord is structurally append-only; update and delete operations are strictly omitted from the repository."),

        ("4. Cryptographic Integrity & Tamper Detection",
         "Every registered evidence item is hashed using chunked SHA-256 (64 KB buffers). During verification, the media hash is recomputed: matching baseline hashes confirm VERIFIED status, while discrepancies trigger MODIFIED status, an audit log entry, and an automatic Rule R4 CRITICAL severity finding. A built-in demo utility safely modifies file bytes to demonstrate tamper detection live."),

        ("5. Deterministic Rule Engine & Multi-Entity Correlation",
         "Rather than unexplainable black-box machine learning, TraceX evaluates four deterministic rules: R1 (>=5 failed logins within 10 min -> MEDIUM), R2 (account lockout following failures -> HIGH), R3 (unusual access then permission change -> HIGH), and R4 (evidence tampering -> CRITICAL). The correlation engine identifies multi-user shared IP origins and temporal proximity without claiming causation."),

        ("6. Reconstructed Incident Timeline",
         "TraceX stitches observed security events and system-generated findings into a unified, monotonically increasing chronological sequence using Timsort in O(n log n) time. Events are grouped by day with explicit evidentiary strength tags: Observed Evidence vs. Detected Indicator vs. System-Generated Finding (never labeled as 'Confirmed Facts')."),

        ("7. Verification & Automated Testing Suite",
         "A complete automated Pytest suite (tests/test_*.py) validates the system with 10 comprehensive tests: T01 (valid hash verification), T02 (tampered evidence alert), T03 (append-only custody immutability), T04 (malformed log fault tolerance), T05 (rule engine R1/R2 triggers), T06 (RBAC 403 Forbidden enforcement), T07 (timeline monotonicity), T08 (multi-entity correlation), T09 (clean template rendering), and T10 (complete 10-minute end-to-end scenario).")
    ]

    for title, text in sections:
        elements.append(Paragraph(title, h1_style))
        elements.append(Paragraph(text, body_style))

    # Test Results Table
    elements.append(Spacer(1, 8))
    elements.append(Paragraph("Automated Test Suite Results (10/10 Passed)", h2_style))
    test_rows = [
        ["Test ID", "Target Module", "Expected Verification", "Status"],
        ["T01", "HashService", "Valid SHA-256 matches baseline -> VERIFIED", "PASSED"],
        ["T02", "HashService", "Tampered file detected -> MODIFIED + R4 CRITICAL", "PASSED"],
        ["T03", "CustodyService", "Append-only insert; past records remain immutable", "PASSED"],
        ["T04", "LogAnalysis", "Malformed CSV rows skipped safely, valid imported", "PASSED"],
        ["T05", "RuleEngine", "5+ failed logins in window triggers R1 (MEDIUM) & R2 (HIGH)", "PASSED"],
        ["T06", "Auth / RBAC", "Unauthorized investigator access yields 403 Forbidden", "PASSED"],
        ["T07", "Timeline", "Mixed out-of-order events sort in O(n log n) order", "PASSED"],
        ["T08", "Correlation", "Multi-user shared IP linked as potentially related", "PASSED"],
        ["T09", "Web Routes", "All pages & detail tabs render cleanly (HTTP 200)", "PASSED"],
        ["T10", "End-to-End", "Full 10-minute scripted scenario executes seamlessly", "PASSED"]
    ]
    test_table = Table(test_rows, colWidths=[55, 95, 305, 65])
    test_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0b2545')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#d0d7de')),
        ('TEXTCOLOR', (3,1), (3,-1), colors.HexColor('#10b981')),
        ('FONTNAME', (3,1), (3,-1), 'Helvetica-Bold')
    ]))
    elements.append(test_table)

    doc.build(elements)
    print(f"[+] Successfully generated academic project report PDF at: {output_path}")

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "docs/TraceX_Project_Report.pdf"
    generate_pdf(out)

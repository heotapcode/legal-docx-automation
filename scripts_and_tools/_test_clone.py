import copy

def clone_paragraph(paragraph):
    """Clone a paragraph and insert it after the original."""
    p = paragraph._p
    new_p = copy.deepcopy(p)
    p.addnext(new_p)
    from docx.text.paragraph import Paragraph
    return Paragraph(new_p, paragraph._parent)

def clone_row(table, row_idx):
    """Clone a row in a table and return the new row."""
    row = table.rows[row_idx]
    new_tr = copy.deepcopy(row._tr)
    row._tr.addnext(new_tr)
    from docx.table import _Row
    return _Row(new_tr, table)

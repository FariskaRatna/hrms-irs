import frappe

@frappe.whitelist()
def get_project_codes(project: str):
    if not project:
        return []
    
    proj = frappe.get_doc("Project", project)

    codes = []
    for row in (proj.get("project_code_detail") or []):
        if row.get("is_active"):
            code = row.get("project_code")
            if code:
                codes.append(code)

    codes = sorted(list(set(codes)))
    return codes
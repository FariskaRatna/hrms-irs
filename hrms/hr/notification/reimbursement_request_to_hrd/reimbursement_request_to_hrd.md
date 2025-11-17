<h3>New Reimbursement Request</h3>

<p>
Employee <strong>{{ doc.employee }}</strong> submitted a new reimbursement request: 
<strong>{{ doc.name }}</strong>.
Please review and approve.
</p>

<h4>Details</h4>

<ul>
    <li>Employee: {{ doc.employee_name }}</li>
    <li>Total Reimbursement: {{ doc.amount }}</li>
    <li>Date: {{ doc.outpatient_date }}</li>
    <li>Diagnosis: {{ doc.diagnosis }}</li>
</ul>

<p>
    <div style="text-align:center; margin-top:20px;">
        <a href="{{ frappe.utils.get_url('/app/reimbursement/' ~ doc.name) }}"
           style="
                padding: 12px 20px;
                background: #1d6df7;
                color: #fff;
                border-radius: 8px;
                text-decoration: none;
                font-size: 14px;
                font-weight: 600;
                display: inline-block;
           ">
            View Request →
        </a>
    </div>

</p>

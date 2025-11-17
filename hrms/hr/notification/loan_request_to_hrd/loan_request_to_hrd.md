<h3>New Loan Request</h3>

<p>
Employee <strong>{{ doc.employee }}</strong> submitted a new loan request: 
<strong>{{ doc.name }}</strong>.
Please review and approve.
</p>

<h4>Details</h4>

<ul>
    <li>Total Loan: {{ doc.total_loan }}</li>
    <li>Installment Amount: {{ doc.installment }}</li>
    <li>Deduction Start Date: {{ doc.deduction_start_date }}</li>
    <li>Reason: {{ doc.reason }}</li>
</ul>

<p>
    <div style="text-align:center; margin-top:20px;">
        <a href="{{ frappe.utils.get_url('/app/loan-application/' ~ doc.name) }}"
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

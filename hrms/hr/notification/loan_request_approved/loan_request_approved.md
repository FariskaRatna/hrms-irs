<h3>Loan Application {{ doc.name }} Approved by HR Manager</h3>

<p>
The loan request <strong>{{ doc.name }}</strong> has been approved by the HR Manager.
HR is now required to review and process it.
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

<h3>Your Loan Request Has Been Submitted</h3>

<p>
Your loan request <strong>{{ doc.name }}</strong> has been fully submitted by HR.
Please wait for payroll processing.
</p>

<h4>Summary</h4>

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



<h3>Your Leave Application Has Been Submitted</h3>

<p>
Your leave application request <strong>{{ doc.name }}</strong> has been fully submitted by HR.
Please wait for payroll processing.
</p>

<p>
    <div style="text-align:center; margin-top:20px;">
        <a href="{{ frappe.utils.get_url('/app/leave-application/' ~ doc.name) }}"
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

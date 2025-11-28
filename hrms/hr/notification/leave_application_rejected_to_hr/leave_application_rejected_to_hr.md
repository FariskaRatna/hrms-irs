<h3>Leave Application {{ doc.name }} Rejected by PM</h3>

<p>
The leave application request <strong>{{ doc.name }}</strong> has been rejected by the Project Manager.
HR is now required to review and process it.
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

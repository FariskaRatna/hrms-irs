<h3>New Business Trip Request</h3>

<p>
Employee <strong>{{ doc.employee }}</strong> submitted a new business trip request: 
<strong>{{ doc.name }}</strong>.
Please review and approve.
</p>

<h4>Details</h4>

<ul>
    <li>Departure Date: {{ doc.from_date }}</li>
    <li>Return Date: {{ doc.to_date }}</li>
    <li>Total Days: {{ doc.total_days }}</li>
    <li>Destination: {{ doc.destination }}</li>
</ul>

<p>
    <div style="text-align:center; margin-top:20px;">
        <a href="{{ frappe.utils.get_url('/app/business-trip/' ~ doc.name) }}"
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

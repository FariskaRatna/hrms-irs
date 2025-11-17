<h3>Overtime Request Update</h3>

<p>
The overtime request <strong>{{ doc.name }}</strong> has been updated.
Please review the information below.
</p>

{% if comments %}
<div style="margin: 10px 0; padding: 10px; background: #f7f7f7; border-left: 3px solid #ccc;">
    <strong>Last Comment:</strong><br>
    "{{ comments[-1].comment }}"<br>
    <em>- {{ comments[-1].by }}</em>
</div>
{% endif %}

<h4>Details</h4>
<ul>
    <li><strong>Employee:</strong> {{ doc.employee }}</li>
    <li><strong>Date:</strong> {{ doc.overtime_date }}</li>
    <li><strong>Total Hours:</strong> {{ doc.total_hours }}</li>
    <li><strong>Status:</strong> {{ doc.status }}</li>
</ul>

<p>
If you need further action, please open the document in the system.
</p>

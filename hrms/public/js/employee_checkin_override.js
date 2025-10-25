// frappe.ui.form.on('Employee Checkin', {
//     refresh(frm) {
//         if (frm.is_new()) {
//             // Langsung ambil geolocation tanpa cek HR Setting
//             if (navigator.geolocation) {
//                 navigator.geolocation.getCurrentPosition(
//                     function(position) {
//                         frm.set_value('latitude', position.coords.latitude);
//                         frm.set_value('longitude', position.coords.longitude);
//                         frm.save();
//                         frappe.show_alert({
//                             message: __('Lokasi otomatis diambil.'),
//                             indicator: 'green'
//                         });
//                     },
//                     function(error) {
//                         frappe.msgprint(__('Gagal ambil lokasi: ') + error.message);
//                     }
//                 );
//             } else {
//                 frappe.msgprint(__('Browser tidak mendukung Geolocation API.'));
//             }
//         }
//     }
// });

$(document).ready(function() {
    console.log('transact_list.js ready');

    let table = $('#dataTable').DataTable({
        processing: true,
        serverSide: true,
        scrollX: true,
        ajax: {
            url: "/transacts/ajx_transact_list/",
            type: 'GET',
            data: function(d) {}
        },
        columns: [
            { data: 'transact_id' },
            { data: 'si_no' },
            { data: 'company' },
            { data: 'date' },
            { data: 'creator' },
            { data: 'location' },
            // { data: 'customer' },
            { data: 'status' },
        ],
        layout: {
            // topStart: 'pageLength',
            // topEnd: 'search',
            // bottomStart: 'info',
            // bottomEnd: 'paging'

            // top2Start: 'pageLength',
            topStart: 'search',
            top2End: 'info',
            topEnd: 'pageLength',

            bottomStart: 'paging',
            bottomEnd: 'info',
            // bottom2Start: 'info',
            // bottom2End: 'paging'
        },
        order: [[0, 'desc']],
        pageLength: 50,
    });
    
});
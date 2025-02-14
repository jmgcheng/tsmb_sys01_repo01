$(document).ready(function() {
    console.log('item_price_adjustment_list.js ready');

    let table = $('#dataTable').DataTable({
        processing: true,
        serverSide: true,
        scrollX: true,
        ajax: {
            url: "/items/ajx_item_price_adjustment_list/",
            type: 'GET',
            data: function(d) {}
        },
        columns: [
            { data: 'item' },
            { data: 'date' },
            { data: 'price' },
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
        order: [[1, 'desc']],
        pageLength: 25,
    });
    
});
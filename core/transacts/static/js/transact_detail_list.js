$(document).ready(function() {
    console.log('transact_detail_list.js ready');

    let table = $('#dataTable').DataTable({
        processing: true,
        serverSide: true,
        scrollX: true,
        ajax: {
            url: "/transacts/details/ajx_transact_detail_list/",
            type: 'GET',
            data: function(d) {
                d.minDate = $('#minDate').val();
                d.maxDate = $('#maxDate').val();
            }
        },
        columns: [
            { data: 'transact_id' },
            { data: 'si_no' },
            { data: 'company' },
            { data: 'date' },
            { data: 'creator' },
            { data: 'location' },
            { data: 'item' },
            { data: 'num_per_unit' },
            { data: 'weight' },
            { data: 'convert_to_kilos' },
            { data: 'quantity' },
            { data: 'delivered_in_kilos' },
            { data: 'price_posted' },
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


    // Custom filter function for date range
    $.fn.dataTable.ext.search.push(function(settings, data, dataIndex) {
        let minDate = $('#minDate').val();
        let maxDate = $('#maxDate').val();
        let transactionDate = data[3]; // Date is in the 4th column (index 3)

        if (minDate) {
            minDate = new Date(minDate);
        }
        if (maxDate) {
            maxDate = new Date(maxDate);
        }
        transactionDate = new Date(transactionDate);

        if (
            (!minDate || transactionDate >= minDate) &&
            (!maxDate || transactionDate <= maxDate)
        ) {
            return true;
        }
        return false;
    });

    // Apply filter when date inputs change
    $('#minDate, #maxDate').on('change', function() {
        table.draw();
    });
    

    $('#resetFilters').on('click', function() {
        $('form select').each(function(index) {
            $(this).val('');
        })
        $('#minDate').val('');
        $('#maxDate').val('');
        $("input[type=radio][value='']").prop('checked', true);
        $("input[type=checkbox][customType='datatableFilter']").prop('checked', false);
        $('.collapse').collapse('hide');
        table.page.len(50).draw();
        table.order([0, 'desc']).draw();
        table.search('').draw();
        table.columns().search('');
        table.draw();
    });

});
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
            { data: 'remarks' },
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

    $('#export-all-btn').click(function () {
        handleExport("/transacts/details/ajx_export_transact_detail_list/");
    });

    $('#export-filtered-btn').click(function () {
        var searchParams = table.ajax.params();
        var queryString = $.param(searchParams);

        handleExport("/transacts/details/ajx_export_filtered_transact_detail_list?" + queryString);
    });

    function handleExport(url) {
        $.ajax({
            url: url,
            method: 'GET',
            beforeSend: function(xhr) {
                disableControls();
                $('#loader').show();
                $('#message').hide();
                $("#message").removeClass();
            },
            success: function (data) {
                $('#loader').hide();
                if (data.status === 'success') {
                    let downloadLink = document.getElementById('download-link');
                    downloadLink.href = '/media/' + data.filename; 
                    downloadLink.download = data.filename; 
                    downloadLink.click();
                    $("#message").addClass("alert alert-success");
                    $('#message').text('File generated and downloaded successfully.');
                    $('#message').show().delay(5000).slideUp(500);
                } else {
                    $("#message").addClass("alert alert-warning");
                    $('#message').text('An error occurred while generating the file.');
                    $('#message').show();
                }
            },
            error: function () {
                $('#loader').hide();
                $("#message").addClass("alert alert-warning");
                $('#message').text('An error occurred while generating the file.');
                $('#message').show();
            },
            complete: function() {
                enableControls();
            }
        });
    }

    function disableControls() {
        $('#export-all-btn').prop('disabled', true);
        $('#export-filtered-btn').prop('disabled', true);
        // $('#import-new-employee-btn').prop('disabled', true);
        // $('#import-update-employee-btn').prop('disabled', true);
    }

    function enableControls() {
        $('#export-all-btn').prop('disabled', false);
        $('#export-filtered-btn').prop('disabled', false);
        // $('#import-new-employee-btn').prop('disabled', false);
        // $('#import-update-employee-btn').prop('disabled', false);
    }

});
$(document).ready(function() {
    console.log('employee_list.js ready');

    localStorage.removeItem('importTaskId');

    var taskId = localStorage.getItem('importTaskId');
    if (taskId) {
        checkTaskStatus(taskId);
        disableControls();
        $('#loader').show();
        $("#message").addClass("alert alert-info");
        $('#message').text('still importing, please wait...');
        $('#message').show();
    }

    let table = $('#employeeTable').DataTable({
        processing: true,
        serverSide: true,
        scrollX: true,
        ajax: {
            url: "/employees/ajx_employee_list/",
            type: 'GET',
            data: function(d) {
                d.position = getCheckedValues('chkPosition');
                d.specialty = getCheckedValues('chkSpecialty');
                d.gender = getCheckedValues('chkGender');
                d.employee_status = getCheckedValues('chkEmployeeStatus');
            }
        },
        columns: [
            { data: 'company_id' },
            { data: 'start_date' },
            { data: 'last_name' },
            { data: 'first_name' },
            { data: 'middle_name' },
            { data: 'position' },
            { data: 'specialties' },
            { data: 'level' },
            { data: 'gender' },
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
        order: [[0, 'asc']],
        pageLength: 25,
    });

    $('input[type=checkbox][name=chkPosition], input[type=checkbox][name=chkSpecialty], input[type=checkbox][name=chkGender], input[type=checkbox][name=chkEmployeeStatus]').change(function() {
        let groupName = $(this).attr("name");
        // get the master checkbox for this group
        let groupAllCheckbox = $('#'+groupName+'-0');
        // 
        // get the other group checkbox that is not master 
        let otherCheckboxes = $('input[type=checkbox][name='+groupName+']').not(groupAllCheckbox);
        
        // is this the master your changing?
        if ($(this).is(groupAllCheckbox)) {
            if (groupAllCheckbox.prop('checked')) {
                otherCheckboxes.prop('checked', true);
            } else {
                otherCheckboxes.prop('checked', false);
            }
        } else {
            if (otherCheckboxes.filter(':checked').length === otherCheckboxes.length) {
                groupAllCheckbox.prop('checked', true);
            } else {
                groupAllCheckbox.prop('checked', false);
            }
        }
        table.draw();
    });

    $('#resetFilters').on('click', function() {
        $('form select').each(function(index) {
            $(this).val('');
        })
        $('#employeeTable_filter input').val('');
        $("input[type=radio][value='']").prop('checked', true);
        $("input[type=checkbox][customType='datatableFilter']").prop('checked', false);
        $('.collapse').collapse('hide');
        table.page.len(25).draw();
        table.order([0, 'asc']).draw();
        table.search('').draw();
        table.columns().search('');
        table.draw();
    });

    $('#export-all-btn').click(function () {
        handleExport("/employees/ajx_export_excel_all_employees");
    });

    $('#export-filtered-btn').click(function () {
        var searchParams = table.ajax.params();
        var queryString = $.param(searchParams);

        handleExport("/employees/ajx_export_excel_filtered_employees?" + queryString);
    });

    $('#import-new-employee-btn').click(function () {
        handleImport("/employees/ajx_import_insert_excel_employees_celery");  
    });

    $('#import-update-employee-btn').click(function () {
        handleImport("/employees/ajx_import_update_excel_employees_celery");    
    });

    function getCheckedValues(name) {
        var values = [];
        $('input[name="' + name + '"]:checked').each(function() {
            let val = $(this).val();

            if (name === 'chkEmployeeStatus' && val === 'ACTIVE') {
                values.push('PROBATION', 'REGULAR');
            }
            else {
                values.push(val);
            }
            return [...new Set(values)];  // Remove duplicates
        });
        return values;
    }

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

    function handleImport(url) {
        let fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.accept = '.xlsx, .xls';
        fileInput.onchange = function(event) {
            let file = event.target.files[0];
            let formData = new FormData();
            formData.append('file', file);

            $.ajax({
                url: url,
                type: 'POST',
                data: formData,
                contentType: false,
                processData: false,
                headers: {
                    'X-CSRFToken': csrfToken,
                },
                beforeSend: function(xhr) {
                    disableControls();
                    $('#loader').show();
                    $('#message').hide();
                    $("#message").removeClass();
                },
                success: function(data) {
                    console.log(data);

                    $('#loader').hide();
                    if(data.status == 'error') {
                        $("#message").addClass("alert alert-warning");
                        $('#message').text(data.message);
                        $('#message').show();
                        enableControls();
                    }
                    else if (data.status == 'started') {
                        $('#loader').show();
                        $("#message").addClass("alert alert-info");
                        $('#message').text(data.message);
                        $('#message').show();
                        localStorage.setItem('importTaskId', data.task_id);
                        checkTaskStatus(data.task_id);
                    }
                    else if (data.status == 'testing') {

                        console.log('here 01')

                    }
                    else {
                        $("#message").addClass("alert alert-info");
                        $('#message').text(data.message);
                        $('#message').show().delay(5000).slideUp(500);
                        table.ajax.reload();
                        enableControls();
                    }
                },
                error: function(jqXHR, textStatus, errorThrown) {
                    $('#loader').hide();
                    $('#message').show();
                    $("#message").addClass("alert alert-warning");
                    $('#message').text(errorThrown);
                    enableControls();
                    console.log(errorThrown);
                },
                complete: function() {}
            });
        };
        fileInput.click();
    }

    function disableControls() {
        $('#export-all-btn').prop('disabled', true);
        $('#export-filtered-btn').prop('disabled', true);
        $('#import-new-employee-btn').prop('disabled', true);
        $('#import-update-employee-btn').prop('disabled', true);
    }

    function enableControls() {
        $('#export-all-btn').prop('disabled', false);
        $('#export-filtered-btn').prop('disabled', false);
        $('#import-new-employee-btn').prop('disabled', false);
        $('#import-update-employee-btn').prop('disabled', false);
    }

    function checkTaskStatus(taskId) {
        $.get('/employees/ajx_tasks_status/' + taskId, function(data) {
            console.log('CTS03: ' + data.status);

            if (data.status == 'SUCCESS') {
                localStorage.removeItem('importTaskId');
                console.log('SUCCESS abcd');

                $('#loader').hide();
                $("#message").removeClass();
                $("#message").addClass("alert alert-success");
                $('#message').text('CTS03: Importing Successful.');
                $('#message').show().delay(5000).slideUp(500);
                table.ajax.reload();

                enableControls();
            } 
            else if (data.status == 'PENDING') {
                console.log('PENDING efg');
                setTimeout(function() {
                    checkTaskStatus(taskId);
                }, 2000);
            } 
            else if (data.status == 'FAILURE') {
                localStorage.removeItem('importTaskId');
                console.log('FAILURE HIJ');

                error_msg = data.message ?? '';

                $('#loader').hide();
                $("#message").removeClass();
                $("#message").addClass("alert alert-warning");
                $('#message').text('CTS01: Importing Fail. ' + error_msg);

                enableControls();
            }
            else if (data.status == 'ERROR') {
                // this else if should almost not happen as data.status will not return 'ERROR'
                localStorage.removeItem('importTaskId');
                console.log('ERROR KLM');

                $('#loader').hide();
                $("#message").removeClass();
                $("#message").addClass("alert alert-warning");
                $('#message').text('CTS02: ' + data.message);

                enableControls();
            }
        });
    }

});
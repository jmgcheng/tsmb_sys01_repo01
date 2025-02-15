window.addEventListener('DOMContentLoaded', () => {
    console.log('transact_form.js ready');
  
    const formset = document.getElementById("formset");
    // id_transact_detail-TOTAL_FORMS auto created by {{ formset.management_form }}
    const totalForms = document.getElementById('id_transact_detail-TOTAL_FORMS');
    const addItemButton = document.getElementById("add-item");
    
    function PlusCaps() {
        nextValue = parseInt(totalForms.value) + 1;
        setNextValue(nextValue);
    }

    function MinusCaps() {
        nextValue = parseInt(totalForms.value) - 1;
        setNextValue(nextValue);
    } 

    function setNextValue(nextValue) {
        totalForms.value = nextValue;
    }

    function renumberAttributes() {
        // const outer = document.getElementById("formset");
        const innerDivs = formset.querySelectorAll(".formset-row");

        innerDivs.forEach(function (div, index) {
            div.querySelectorAll('label, select, input').forEach(function (element) {
                const attributes = ['for', 'name', 'id'];

                attributes.forEach(function (attr) {
                    let value = element.getAttribute(attr);
                    if (value) {
                        // Replace the numeric part of the attribute with the new index
                        value = value.replace(/\d+/g, index);
                        element.setAttribute(attr, value);
                    }
                });
            });
        });
    }

    function sureSingleDetail() {
        if ($('.formset-row:visible').length == 1) {
            console.log('disable please');
            $('.formset-row:visible').find('.delete-row').prop('disabled', true);
        }
        else {
            console.log('enable please');

            $('.formset-row:visible').find('.delete-row').prop('disabled', false);
        }
    }

    sureSingleDetail();

    addItemButton.addEventListener("click", function () {
        const firstRow = formset.querySelector(".formset-row");
        if (firstRow) {
            const newRow = firstRow.cloneNode(true);

            formset.appendChild(newRow);

            $(newRow).find('select').val('');
            $(newRow).find('input[type=number]').val(0);
            $(newRow).find('input[type=checkbox]').prop('checked', false);
            $(newRow).show();

            PlusCaps();
            renumberAttributes();
            sureSingleDetail();
        }
    });

    formset.addEventListener("click", function (event) {
        if (event.target.classList.contains("delete-row")) {
            let row = event.target.parentElement;
            // get closest parent
            row = $(row).closest('.formset-row')

            $(row).find('input[type=checkbox]').prop('checked', true);
            // just hide row so backend can log what to delete
            $(row).hide();

            sureSingleDetail();
        }
    });

});

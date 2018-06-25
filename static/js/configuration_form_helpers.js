function set_select_value(element_id, text, value) {
    var elem = document.getElementById(element_id);
    var option = document.createElement("option");
    option.text = text;
    option.value = value;
    option.selected = true;
    elem.add(option);
}

function setFields(agency_config) {
    if (!agency_config) return;

    let arr = ['agency', 'username', 'password', 'input_url', 'domain', 'sync_at', 'path'];

    for(item of arr) {
        if (item === 'domain') {
            document.getElementById(item).value = agency_config[item]._id;
        } else {
            document.getElementById(item).value = agency_config[item];
        }
    }

    document.getElementById("publish").checked = agency_config.publish === "on";

    var formValidation = Array.from(document.querySelectorAll('[required]')).filter(x => x.value === "").length === 0;
    document.querySelector('.mapping-btn ').disabled = !formValidation;

    set_select_value('content_type', agency_config.content_type.name, agency_config.content_type._id);

}

function setContentTypes(token, management_api) {
    var token = token;
    var management_api = management_api;
    var url = management_api + '/domains/' + document.getElementById('domain').value + '/content-types/_query';
    $.ajax({
        url: url,
        type: 'POST',
        data: "{}",
        headers: {
            "Authorization": 'Bearer ' + token,
            "Content-Type": "application/json"
        },
        dataType: 'json',
        success: function (data) {
            var elem = document.getElementById('content_type');
            elem.options.length = 0;
            data['data']['items'].forEach(function (content_type, i) {
                var option = document.createElement("option");
                option.text = content_type['name'];
                option.value = content_type['_id'];
                option.selected = i === 0;
                elem.add(option);
            })
        },
        error: function (data) {
            console.info(data);
            console.log(management_api);
            console.log(token);
        }
    });

}

function getFieldDefinition(content_type_id, domain_id, agency_name) {
    var url = '/configs/mapping';

    $.ajax({
        url: url,
        type: 'POST',
        data: {
            'content_type_id': content_type_id,
            'domain_id': domain_id,
            'agency': agency_name
        },
        dataType: 'json',
        success: function (data) {
            labelListHtml =
                "<div class='row'>" +
                "<div class='col-md-4'>" +
                "<label><b>Content Type's Fields</b></label>" +
                "</div>" +
                "<div class='col-md-6'>" +
                "<label><b>RSS's Fields</b></label>" +
                "</div>" +
                "</div><br>";

            data.field_definitions.splice(0, 0, {
                'name': 'Başlık',
                'field_id': 'title',
                'type': 'string',
                'required': 'true'
            });
            data.field_definitions.splice(1, 0, {
                'name': 'Açıklama',
                'field_id': 'description',
                'type': 'string',
                'required': 'true'
            });
            data.field_definitions.forEach(function (item) {


                itemDivStr = "<div class='row' id='mapping_form_div'><div class='col-md-4' id='mapping_form_label' style='margin-top: 12px;'>";
                itemLabelStr = "<label>" + item.name + ":" + "</label>";
                itemDivEndStr = "</div>";

                selectItems = '<div class="form-group col-md-6"><select name="' + item.field_id + '" id="' + item.name + '" class="form-control"';
                if (item.required) {
                    selectItems += " required><option value=''></option>";
                } else {
                    selectItems += "><option value=''></option>;"
                }
                data.agency_fields.forEach(function (selectItem) {
                    itemSelectPart = "<option value=" + selectItem + ">" + selectItem + "</option>";
                    selectItems += itemSelectPart;
                });
                selectItems += "</select></div>";

                labelListHtml += itemDivStr + itemLabelStr + itemDivEndStr + selectItems + itemDivEndStr;
            });
            document.getElementById("mapping_form").innerHTML = labelListHtml;

            return data
        },
        error: function (data) {
            console.info(data);
        }
    });
}

function SetSelectValue(element_id, text, value) {
    elem = document.getElementById(element_id);
    option = document.createElement("option");
    option.text = text;
    option.value = value;
    option.selected = true;
    elem.add(option);
}

function setFields(agency_config) {
    if (!agency_config) return;

    arr = [
        'agency_name', 'username', 'password',
        'cms_username', 'cms_password', 'input_url', 'app_id', 'app_secret',
        'domain', 'sync_at', 'expire_time', 'path', 'username_parameter', 'password_parameter'
    ];

    for (item of arr) {
        if (document.getElementById(item)) {
            document.getElementById(item).value = item === 'domain' ? agency_config[item]._id : agency_config[item];
        }
    }

    formValidation = Array.from(document.querySelectorAll('[required]')).filter(x => x.value === "").length === 0;
    document.querySelector('.mapping-btn ').disabled = !formValidation;

    showAuthFields(agency_config.agency_name);

    SetSelectValue('content_type', agency_config.content_type.name, agency_config.content_type._id);

}

function setContentTypes(token, management_api) {
    url = management_api + '/domains/' + document.getElementById('domain').value + '/content-types/_query';
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
            elem = document.getElementById('content_type');

            if(elem.selectedIndex>0)
                val = elem.options[elem.selectedIndex].value;

            elem.options.length = 0;
            data['data']['items'].forEach(function (content_type, i) {
                option = document.createElement("option");
                option.text = content_type['name'];
                option.value = content_type['_id'];
                elem.add(option);
            })
            if (val) {
                elem.value = val
            }
        },
        error: function (data) {
            console.info(data);
            console.log(management_api);
            console.log(token);
        }
    });

}

function getFieldDefinition(content_type_id, domain_id, agency_name, agency_config) {
    url = '/configs/mapping';

    agency_config_id = window.location.href.toString().split(window.location.host)[1].split('configs/')[1];

    $.ajax({
        url: url,
        type: 'POST',
        data: {
            'content_type_id': content_type_id,
            'domain_id': domain_id,
            'agency_name': agency_name,
            'agency_config_id': (agency_config_id !== 'create') ? agency_config_id : null
        },
        dataType: 'json',
        success: function (data) {
            window.field_definitions = data.field_definitions;
            labelListHtml =
                "<div class='row'>" +
                "<div class='col-md-4'>" +
                "<label><b>Content Type's Fields</b></label>" +
                "</div>" +
                "<div class='col-md-6'>" +
                "<label><b>RSS's Fields</b></label>" +
                "</div>" +
                "</div><br>";

            window.field_definitions.splice(0, 0, {
                'name': 'Başlık',
                'field_id': 'title',
                'type': 'string',
                'required': 'true'
            });
            window.field_definitions.splice(1, 0, {
                'name': 'Açıklama',
                'field_id': 'description',
                'type': 'string',
                'required': 'true'
            });

            window.field_definitions.forEach(function (item) {

                itemDivStr = "<div class='row' id='mapping_form_div'><div class='col-md-4' id='mapping_form_label' style='margin-top: 12px;'>";
                itemLabelStr = "<label>" + item.name + ":" + "</label>";
                itemDivEndStr = "</div>";

                selectItems = '<div class="form-group col-md-6"><select onchange="getRssResponse();" name="' + item.field_id + '" id="' + item.field_id + '" class="form-control"';
                selectItems += "><option value=''></option>";

                data.agency_fields.forEach(function (selectItem) {
                    itemSelectPart = "<option value=" + selectItem + ">" + selectItem + "</option>";
                    selectItems += itemSelectPart;
                });
                selectItems += "</select></div>";

                labelListHtml += itemDivStr + itemLabelStr + itemDivEndStr + selectItems + itemDivEndStr;

            });

            document.getElementById("mapping_form").innerHTML = labelListHtml;

            document.getElementById('preview_button').classList.remove('d-none');

            field_ids = [];
            len = window.field_definitions.length;
            for (i = 0; i < len; i++) {
                field_ids.push(window.field_definitions[i].field_id);
            }

            if (agency_config) {
                field_ids.forEach(function (field_id) {
                    document.getElementById(field_id).value = agency_config[field_id];
                });
            }

            return data
        },
        error: function (data) {
            console.info(data);
        }
    });
}

function rssResponse(input_url, username, password, app_id, app_secret, agency_name) {
    url = '/rss';

    $.ajax({
        url,
        type: 'POST',
        dataType: 'json',
        data: {
            'input_url': input_url,
            'username': username,
            'password': password,
            'app_id': app_id,
            'app_secret': app_secret,
            'agency_name': agency_name
        },
        success: function (data) {

            field_ids = [];
            len = window.field_definitions.length;
            for (i = 0; i < len; i++) {
                field_ids.push(window.field_definitions[i].field_id);
            }

            mapped_fields = {};
            field_ids.forEach(function (field_id) {
                mapped_fields[field_id] = document.getElementById(field_id).value;
            });

            pre_json = {};
            for (j = 0; j < len; j++) {
                pre_json[field_ids[j]] = data[mapped_fields[field_ids[j]]];
            }

            document.getElementById('preview_row').innerHTML = "<pre style='white-space: pre-wrap'>" + JSON.stringify(pre_json, undefined, 4) + "</pre>";
            document.getElementById('preview_row').classList.remove('d-none');

            document.querySelector('#preview_button').disabled = false;
            document.querySelector('#preview_button').innerHTML = 'Preview';
            document.getElementById('preview_row').scrollIntoView();
        },
        error: function (data) {
            console.log(data)
        }
    })}



function showAuthFields(agency_name) {
    if (['IHA'].includes(agency_name)){
        document.getElementById('aws-auth-fields').classList.replace('inline-flex', 'd-none');
        document.getElementById('auth_fields').classList = ['show-all'];
        inputs = document.getElementById('aws-auth-fields').querySelectorAll('input');
        inputs.forEach(function (input_element) {
            input_element.required = '';
        });
    } else if (['DHA', 'Reuters', 'AA', 'AP'].includes(agency_name)) {
        document.getElementById('aws-auth-fields').classList.replace('inline-flex', 'd-none');
        document.getElementById('auth_fields').classList = ['show-main'];
        inputs = document.getElementById('aws-auth-fields').querySelectorAll('input');
        inputs.forEach(function (input_element) {
            input_element.required = '';
        });
    } else if (['HHA'].includes(agency_name)) {
        document.getElementById('auth_fields').classList = ['d-none'];
        inputs = document.getElementById('auth_fields').querySelectorAll('input');
        inputs.forEach(function (input_element) {
            input_element.required = '';
        });

        document.getElementById('aws-auth-fields').classList.replace('d-none', 'inline-flex');
    }
    else {
        inputs = document.getElementById('auth_fields').querySelectorAll('input');
        inputs.forEach(function (input_element) {
            input_element.value = '';
        });
        document.getElementById('auth_fields').classList = [];
    }
}
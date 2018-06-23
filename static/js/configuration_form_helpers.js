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

    document.getElementById('name').value = agency_config.name;
    document.getElementById('username').value = agency_config.username;
    document.getElementById('password').value = agency_config.password;
    document.getElementById('input_url').value = agency_config.input_url;
    document.getElementById("domain").value = agency_config.domain._id;
    document.getElementById("sync_at").value = agency_config.sync_at;
    document.getElementById("path").value = agency_config.path;
    if (agency_config.publish === "on") {
        document.getElementById("publish").checked = true;
    }
    else {
        document.getElementById("publish").checked = false;
    }
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

function getFieldDefinition(content_type_id, domain_id, input_url) {
    var url = '/configs/mapping';

    $.ajax({
        url: url,
        type: 'POST',
        data: {
            'content_type_id': content_type_id,
            'domain_id': domain_id,
            'input_url': input_url
        },
        dataType: 'json',
        success: function (data) {
            labelListHtml = "<hr><div class='row'><div class='col-md-4'><label>Content Type</label></div><div class='col-md-6'><label>Agency Fields</label></div></div><br>";
            data.field_definitions.forEach(function (item) {


                itemDivStr = "<div class='row' id='mapping_form_div'><div class='col-md-4' id='mapping_form_label' style='margin-top: 12px;'>";
                itemLabelStr = "<label>" + item.name + ":" + "</label>";
                itemDivEndStr = "</div>";

                selectItems = "<div class='col-md-6'><select name=" + item.name + " id=" + item.name + "class='form-control'";
                if (item.required) {
                    selectItems += " required><option value=''></option>";
                } else {
                    selectItems += "><option value=''></option>;"
                }
                data.agency_fields.forEach(function (selectItem)
                {
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

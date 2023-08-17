let newWindow;
const shapeData = document.getElementById('shape_data');
const formInput = document.getElementById('shape');
const lengInput = document.getElementById('length');
const widtInput = document.getElementById('width');

const openEditWindow = (editorUrl) => {
    const params = `scrollbars=no,resizable=no,status=no,location=no,toolbar=no,menubar=no,width=700,height=500,top=200,left=400`;
    if (formInput.value.length == 0||formInput.value == "undefined"){
        newWindow = window.open(editorUrl, 'sub', params);
    }
    else{
        newWindow = window.open(editorUrl+"?"+formInput.value, 'sub', params);
    }
};

const openNewWindow = (editorUrl) => {
    const params = `scrollbars=no,resizable=no,status=no,location=no,toolbar=no,menubar=no,width=700,height=500,top=200,left=400`;
    newWindow = window.open(editorUrl, 'sub', params);
};

const sendMessage = () => {
    newWindow.postMessage({ foo: 'bar' }, '*');
};

const closeWindow = (shape_selected, tot_len) => {
    window.opener.postMessage({shp: shape_selected, len: tot_len}, '*');
    window.close();
};

const refreshWindow = () => {
    setTimeout(function(){
   window.opener.location.reload();
}, 1000);
setTimeout("window.close()",1000)
};

window.addEventListener('message', (event) => {
    shapeData.value = event.data.shp;
    formInput.value = event.data.shp;
    lengInput.value = event.data.len;
    if (event.data.shp != '332'){
        calc_weight();
    }
});

function confirmDel() {
  let text = "Are you sure?";
  if (confirm(text) == true) {
    window.location.href = "close?delete";
  }
}

function findTotal(src, target){
    var arr = document.getElementsByClassName(src);
    var tot=0;
    for(var i=0;i<arr.length;i++){
        if(parseFloat(arr[i].value))
            tot += parseFloat(arr[i].value);
    }
    document.getElementById(target).value = tot;
}

function findTotal2(src, target, inputId){
    var inputEl = document.getElementById(inputId)
    var arr = document.getElementsByClassName(src);
    var tot=0
    if (parseFloat(inputEl.value)){
    tot += parseFloat(inputEl.value);
    }
    for(var i=0;i<arr.length;i++){
        if(parseFloat(arr[i].textContent))
            tot += parseFloat(arr[i].textContent);
    }

    if(tot > 0){
        document.getElementById(target).value = tot;
    }
}
var temp = 0
function addInput(div_id, val){
    var container = document.getElementById(div_id);
    var input = document.createElement("input");
    input.type = "number";
    input.name = div_id.replace('_container', temp);
    temp += 1
    input.setAttribute('class', 'form-control');
    input.setAttribute('onkeydown', "return event.key != 'Enter';");
    input.setAttribute('onkeyup', "");
    if(val){
        input.setAttribute('value', val);
    }
    if(div_id.includes("pitch")){
        input.setAttribute('placeholder', 'פסיעה');
    }
    if(div_id.includes("length")){
        input.setAttribute('placeholder', 'אורך');
    }
    if(div_id.includes("width")){
        input.setAttribute('placeholder', 'רוחב');
    }
    container.appendChild(input);
}

function copyLastRow(dict, dataToDisplay){
    dataToDisplay['shape_data'] = 1;
    dataToDisplay['length'] = 1;
    dataToDisplay['quantity'] = 2;
    dataToDisplay['weight'] = 2;
    for(item in dataToDisplay){
        if(dataToDisplay[item] != 2 && dataToDisplay[item] != 4){
            try {
                document.getElementById(item).value = dict[item];
            }
            catch (error) {
                document.getElementById(item).value = dict[item].map(String);
                console.error(error);
            }
        }
    }
    document.getElementById('quantity').focus();
}

function calc_weight(){
diam = document.getElementById('diam');
qnt = document.getElementById('quantity');
weight = document.getElementById('weight');
weights_list = {
    "6": 0.222,
    "8": 0.395,
    "10": 0.617,
    "12": 0.888,
    "14": 1.208,
    "16": 1.578,
    "18": 1.998,
    "20": 2.466,
    "22": 2.98,
    "25": 3.85,
    "28": 4.834,
    "32": 6.31,
    "36": 7.986,
    "5.5": 0.2,
    "6.5": 0.27
  };
    leng = lengInput.value;
    if (diam.value){
        weight.value = (leng * qnt.value * weights_list[diam.value] / 100).toFixed(1);
    }
}
function formSubmit(){
    form = document.getElementById("input_form");
        if (form.checkValidity()){
            form.submit();
        }
}

var do_once = 0
function focusNext(inputIndex) {
    inputNames = dtd_order;
    if (event.keyCode === 13){
        var safety = 0;
        while (safety < 20){
            inputIndex += 1;
            if (inputIndex >= inputNames.length && do_once == 0 ){
                form = document.getElementById("input_form");
                if (form.checkValidity() && do_once==0){
                    form.submit();
                    do_once = 1;
                }
                else{
                    inputIndex = 0;
                    if (shapeData.value == "") {
                        alert("נדרשים פרטי צורה");
                    }
                }
            }
            if (datatodisp[inputNames[inputIndex]] != 2 && document.getElementById(inputNames[inputIndex]) !== null){
                inputName = inputNames[inputIndex];
                break
            }
            safety += 1;
        }
        document.getElementById(inputName).focus();
    }
}

function runScanner(order_id){
try{
    fetch("/file_listener", {
      method: "POST"
    });
    }catch (error){
    window.alert("Server Error", error);
}
try{
    fetch("http://localhost:5000/scanner?"+order_id, {
      method: "POST"
    });
}catch (error){
    window.alert("Client Error", error);
}
};
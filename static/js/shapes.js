let newWindow;
const shapeData = document.getElementById('shape_data');
const formInput = document.getElementById('shape');
const lengInput = document.getElementById('length');
const widtInput = document.getElementById('width');
const diamInput = document.getElementById('diam');

const openEditWindow = (editorUrl) => {
    const params = `scrollbars=no,resizable=no,status=no,location=no,toolbar=no,menubar=no,width=700,height=500,top=200,left=400`;
    editorUrl += '?';
    //if (formInput.value.length == 0&&formInput.value == "undefined"){
    if (formInput.value.length != 0&&formInput.value != "undefined"){
        //newWindow = window.open(editorUrl, 'sub', params);
        editorUrl += 'shape='+formInput.value;
    }
    if (diamInput.value.length != 0&&diamInput.value != "undefined"){
        //newWindow = window.open(editorUrl, 'sub', params);
        editorUrl += '&diam='+diamInput.value;
    }
    //else{
        //newWindow = window.open(editorUrl+"?"+formInput.value, 'sub', params);
    //}
    newWindow = window.open(editorUrl, 'sub', params);
};

const openNewWindow = (editorUrl) => {
    const params = `scrollbars=no,resizable=no,status=no,location=no,toolbar=no,menubar=no,width=700,height=500,top=200,left=400`;
    newWindow = window.open(editorUrl, 'sub', params);
};

const sendMessage = () => {
    newWindow.postMessage({ foo: 'bar' }, '*');
};

const closeWindow = (shape_selected, tot_len, shape_dt) => {
    window.opener.postMessage({shp: shape_selected, len: tot_len, shapedt: shape_dt}, '*');
    window.close();
};

const refreshWindow = () => {
    setTimeout(function(){
   window.opener.location.reload();
}, 1000);
setTimeout("window.close()",1000)
};

window.addEventListener('message', (event) => {
    shapeData.value = event.data.shapedt;
    formInput.value = event.data.shp;
    lengInput.value = event.data.len;
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

function addInput(vect){
    all_in = document.getElementsByClassName(vect+'_length');
    for(i=0;i<all_in.length;i++){
        if(all_in[i].hidden){
            all_in[i].hidden = false;
            document.getElementById(vect+'_pitch'+(i+1)).hidden = false;
            break;
        }
    }
}

function copyLastRow(dict, dataToDisplay){
    dataToDisplay['shape_data'] = 1;
    dataToDisplay['length'] = 1;
    dataToDisplay['quantity'] = 2;
    dataToDisplay['weight'] = 2;
    for(item in dataToDisplay){
        if(dataToDisplay[item] != 2 && dataToDisplay[item] != 4){
            try {
                if (dict[item])
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
    "6": 0.223,
    "8": 0.398,
    "10": 0.621,
    "12": 0.883,
    "14": 1.213,
    "16": 1.582,
    "18": 2,
    "20": 2.466,
    "22": 2.98,
    "25": 3.864,
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
// reorder func
    inputNames = dtd_order;
    if (event.keyCode === 13){
        var safety = 0;
        while (safety < 80){
            form = document.getElementById("input_form");
            if (form.checkValidity() && do_once==0){
                do_once = 1;
                form.submit();
                break
            }
            inputIndex += 1;
            if (inputIndex >= inputNames.length && do_once == 0){
                if (inputIndex >= inputNames.length){
                    inputIndex = 0;
                }
                //if (shapeData){
                //    if (shapeData.value == "") {
                //        alert("נדרשים פרטי צורה");
                //    }
                //}

            }
            element = document.getElementById(inputNames[inputIndex])
            if (datatodisp[inputNames[inputIndex]] != 2 && element !== null && element.hidden == false){
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

function delete_rows(){
    let selected = []
    select = document.getElementsByClassName('select');
    for(i=0;i<select.length;i++){
        item = select[i];
        if (item.checked) {
            selected.push(item.value)
        }
    }
    if(selected.length > 0){
        document.getElementById('delete_rows_btn').disabled = true;
        form = document.getElementById('input_form');
        form.action = location.href='\\delete_rows'
        form.submit();
    }
}


var expanded = false;

function showCheckboxes(elem_id) {
  var checkboxes = document.getElementById(elem_id);
  if (!expanded) {
    checkboxes.style.display = "block";
    expanded = true;
  } else {
    checkboxes.style.display = "none";
    expanded = false;
  }
}

function setCookie(cname, cvalue, exdays) {
  const d = new Date();
  d.setTime(d.getTime() + (exdays*24*60*60*1000));
  let expires = "expires="+ d.toUTCString();
  document.cookie = cname + "=" + cvalue + ";" + expires + ";path=/";
}

function getCookie(cname) {
  let name = cname + "=";
  let decodedCookie = decodeURIComponent(document.cookie);
  let ca = decodedCookie.split(';');
  for(let i = 0; i <ca.length; i++) {
    let c = ca[i];
    while (c.charAt(0) == ' ') {
      c = c.substring(1);
    }
    if (c.indexOf(name) == 0) {
      return c.substring(name.length, c.length);
    }
  }
  return "";
}

function calc_length(){
    s1 = document.getElementById('spiral').value
    s2 = document.getElementById('spiral_1').value
    s3 = document.getElementById('spiral_2').value
    s4 = document.getElementById('spiral_3').value
    sum = 0;
    if (s1){sum=sum+parseInt(s1)}
    if (s2){sum=sum+parseInt(s2)}
    if (s3){sum=sum+parseInt(s3)}
    if (s4){sum=sum+parseInt(s4)}
    bars_len = document.getElementById('bars_len')
    if (sum>0){
        bars_len.value = sum;
        bars_len.min = sum;
    }
}

// 提取id参数
name = "id"
callback = "callback"
var reg = new RegExp("(^|&|\\?)" + name + "=([^&]*)(&|$)", "i")
iid = window.location.href.match(reg)[2]
ajaxUrl = "https://tx.xujipm.com/getwords.py?iid="+iid

// 增加文字云容器
div = document.createElement("div");
div.id = "main"
div.style = "width:100%;height:150px"
div.innerText = "echarts init..."
$("#detail").prepend(div)
//$("#reviews > div").prepend(div)

// echart 初始化
var myChart = echarts.init(document.getElementById('main'));
var option = {
    tooltip: {},
    series: [{
        type: 'wordCloud',
        gridSize: 25,
        sizeRange: [15,50],
        rotationRange:[0,20],
        shap:'cardioid',
        textStyle: {
            normal: {
                color: function(){
                    return 'rgb(' + [
                        Math.round(Math.random() * 160),
                        Math.round(Math.random() * 160),
                        Math.round(Math.random() * 160)
                    ].join(',')+')';
                }
            },
            emphasis: {
                shadowBlur: 10,
                shadowColor: '#333'
            }
        },
        data: []
    }]
};

myChart.showLoading();
getWords();

function getWords(){
    $.ajax({
        url: "https://tx.xujipm.com/getwords.py",
        type: 'GET',/*
        jsonp: "callback",*/
        dataType: 'json',/*
        jsonpCallback: "jsonp2375",*/
        contentType: "application/json; charset=utf-8",
        crossDomain: true,
        async: true,
        data: {
            iid: iid
        },
        success: function (data) {
            //console.log(data.result,option.series[0].data.length,data.list.fenci)

            if(data.list.fenci=="waite"||Object.keys(data.list.fenci).length==0){
                setTimeout(function(){getWords()},1000);
            }else{
                for (var name in data.list.fenci) {
                    option.series[0].data.push({
                        name: name,
                        value: data.list.fenci[name]
                    });
                }
                myChart.hideLoading();
                myChart.setOption(option);
            }
        },
        error: function(q,ts,et) { 
            console.log(ts+":"+et);
        }
    });
}

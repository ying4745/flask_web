// 个人头像下拉
$(document).ready(function(){
    $(".dropdown").hover(function(){
        $(this).find('ul:first').css({visibility: "visible",display: "none"}).slideDown("normal");
    },function(){
        $(this).find('ul:first').css({visibility: "hidden"});
    });
});

// 返回顶部
$(function(){
        $(function () {
            //当点击跳转链接后，回到页面顶部位置
            $("#back-to-top").click(function(){
                //$('body,html').animate({scrollTop:0},500); 如使用这个返回顶部会闪现一次
            if ($('html').scrollTop()) {
                $('html').animate({ scrollTop: 0 }, 500);
                return false;
            }
            $('body').animate({ scrollTop: 0 }, 500);
                return false;
        });
            //当滚动条的位置处于距顶部100像素以下时，跳转链接出现，否则消失
            $(window).scroll(function(){
                if ($(window).scrollTop()>100){
                    $("#back-to-top").fadeIn(400);
                }
                else
                {
                    $("#back-to-top").fadeOut(800);
                }
            });
        });
});

// flash消息闪现
$(function() {
    $(".alert-warning").fadeTo(3000, 400).fadeOut(1000);
});

// 导航栏高亮
var path = location.pathname;
var path_status = false;
$('.menu a').each(function () {
    if (path === $(this).attr('href')&&$(this).attr('href') !== '') {
        $(this).addClass('menu_active');
        path_status = true;
    } else {
        $(this).removeClass('menu_active');
    }
});
if (!path_status) {
    $('.menu a').eq(0).addClass('menu_active');
};

// 个人资料分栏
$(function() {
    $('.profile-nav li').eq(0).addClass("act");
    $('.profile-nav li').each(function(){
        $(this).click(function(){
            $(this).addClass("act").siblings().removeClass("act");
        })
    })
});

// 个人资料分栏下显示
function showAtBottom(url){
    $.ajax({
        type: "GET",
        url: url,
        dataType: "html",
        success : function(data) {
            $(".profile-content").html(data);
        },
        error : function(status) {
            $(".profile-content").html("<h3>获取数据失败!</h3>" + status);
        }
    });
};

// 关注和取消关注
function follow(username,id) {
    var btn_this = $('#'+id);
    if (!btn_this.hasClass('btn_follow_red')) {
        $.get('/follow/'+username, function(data,status) {
            if (status=='success') {
                btn_this.text('取消关注').addClass('btn_follow_red');
            } else {
                btn_this.text('异常');
            }
        });
    }
    else {
        $.get('/unfollow/'+username, function(data,status) {
            if (status=='success') {
                btn_this.text('+ 关注').removeClass('btn_follow_red');
            } else {
                btn_this.text('异常');
            }
        });
    }
};

// 屏蔽与解禁评论
function com_disa(id) {
    var btn_this = $('#'+id);
    if (!btn_this.hasClass('btn_follow_red')) {
        $.get('/moderate/enable/'+id, function(data,status) {
            if (status=='success') {
                btn_this.text('屏蔽').addClass('btn_follow_red');
            } else {
                btn_this.text('异常');
            }
        });
    }
    else {
        $.get('/moderate/disable/'+id, function(data,status) {
            if (status=='success') {
                btn_this.text('解禁').removeClass('btn_follow_red');
            } else {
                btn_this.text('异常');
            }
        });
    }
};
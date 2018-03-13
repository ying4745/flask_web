// 导航栏下拉
$(function() {
    $(".menu ul").css({display: "none"}); // Opera Fix
    $(".menu li").hover(function(){
        $(this).find('ul:first').css({visibility: "visible",display: "none"}).slideDown("normal");
    },function(){
        $(this).find('ul:first').css({visibility: "hidden"});
    });
});
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

$(function() {
    $(".alert-warning").fadeTo(3000, 400).fadeOut(1000);
});
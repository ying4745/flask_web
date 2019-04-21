
// 展开 收起评论条件判断
function add_expand_btn() {
    var com_boxes = $('.max_content').children();
    for (var i=0;i<com_boxes.length;i++) {
        com_box = $(com_boxes[i]);
        if (com_box.height() > 170) {
            com_box.parent().after('<botton onclick="expand_com(this)" class="expand_btn com_btn">展开评论</botton>')
        }
    }
}

// ajax GET请求评论数据
function ajax_comments() {
    var article_id = $('#comment_box').attr('a_id');
    var url = '/article/' + article_id + '/comments';
    $.get(url, function (data, status) {
        if (status === 'success'){
            $('#comment_box').html(data);

            add_expand_btn();
        } else {
            $('#comment_box').html('<h3>加载评论出错</h3>' + status);
        }
    });
}

// ajax发送评论
$('#comment_ajax_form').submit(function (e) {
    e.preventDefault();  // 阻止表单的默认提交行为

    $.ajax({
        url: '/article/comment',
        type: 'POST',
        datatype: 'json',
        data: $(this).serializeArray(),
        success: function (res) {
            if (res.errno === '0'){
                ajax_comments()
            } else {
                alert(res.errmsg);
            }

        },
        error: function () {
            alert('评论出错！')
        }
    });
    $('#input_res').trigger("click"); // 触发重置按钮
    $('#form_sub').blur(); // 移除发布按钮的焦点
});

// 子评论发送
function bot_com(obj) {
    var thisobj=$(obj);
    var com_id = thisobj.parent().next().attr('comid');
    var article_id = thisobj.parent().next().attr('articleid');
    var com_content = thisobj.prev().text();
    params = {'com_id':com_id, 'article_id':article_id, 'com_content':com_content};
    $.post('/article/add/comment', params, function (res) {
        if (res.errno == '0') {
            ajax_comments();
        } else {
            if (res.errmsg == '用户未登陆') {
                window.location.href='/auth/login';
            } else {
                alert(res.errmsg)
            }
        };
    });
};

// 展开 收起评论按钮
function expand_com(obj) {
    var show_con = $(obj);
    var com_box = show_con.prev().children();

    if (show_con.prev().css('max-height') > '170px') {
        show_con.prev().css('max-height','170px');
        show_con.text('展开评论');
    } else {
        show_con.prev().css('max-height',com_box.outerHeight(true));
        show_con.text('收起评论');
    }
};

// 点赞
function add_favorite(current_elem, fav_id, fav_type) {
    var params = {'fav_id':fav_id, 'fav_type':fav_type};
    var url = "/add/favorite";
    $.post(url, params, function (res) {
        if(res.errno == '0'){
            var fav_img = current_elem.children('i');
            if (fav_img.hasClass('icon-dianzan')){
                fav_img.removeClass('icon-dianzan');
                fav_img.addClass('icon-dianzan1');
                current_elem.children('span').text('(' + res.data + ')');
            } else {
                fav_img.removeClass('icon-dianzan1');
                fav_img.addClass('icon-dianzan');
                current_elem.children('span').text('(' + res.data + ')');
            };
        } else {
            if (res.errmsg == '用户未登陆') {
                window.location.href='/auth/login';
            } else {
                alert(res.errmsg)
            }
        }
    })
};

// 评论点赞和取消点赞
function isComFavorite(obj) {
    var thisObj = $(obj);
    var fav_id = thisObj.parents('ul').nextAll('span').attr('comid');
    add_favorite(thisObj, fav_id, 'comment')
};

// 文章点赞和取消点赞
function isArticleFavorite(obj) {
    var thisObj = $(obj);
    var fav_id = thisObj.parent().attr('articleid');
    add_favorite(thisObj, fav_id, 'article')
};

$(function () {
    // 加载评论
    ajax_comments();

    // 绑定评论回复按钮事件
    $(document).on('click', '.reply_btn', function() {
        // 将展开的评论收起来
        $('.reply_textarea').parents('.max_content').css('max-height', '170px');
        $('.reply_textarea').parents('.max_content').next().text('展开评论');
        // 移除其他评论下的子评论框
        $('.reply_textarea').remove();
        // 当前点击按钮下添加子评论框
        $(this).closest('ul').next().after(
        '<div class="reply_textarea"><div id="com_text" class="com_text" contenteditable="true"></div>' +
        '<input type="botton" class="com_btn" onclick="bot_com(this)" style="width: 28px;" value="评论"></div>'
        );
        // 输入框获得焦点
        $('.com_text').focus();

        // 回复评论时，完全显示评论和表单
        var com_box_obj = $('.reply_textarea').parents('.max_content').children();
        $('.reply_textarea').parents('.max_content').css('max-height', com_box_obj.outerHeight(true));
        if ($('.reply_textarea').parents('.max_content').next().prop('tagName') === 'BOTTON') {
            $('.reply_textarea').parents('.max_content').next().text('收起评论');
        }
    });

});

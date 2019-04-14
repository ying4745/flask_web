/**
 * Created by a12345 on 2018/12/6.
 */

// 生成评论html
function makeCommentTree(comment_list) {
    var htmls = '';
    $.each(comment_list, function (i, comment) {

        var comment_str = '<div class="comment_item"><ul class="comment_title clearfix">' +
            '<li><a href="#"><img src="' +
            comment['author_img'] +
            '" class="portrait"></a></li>' +
            '<li><a href="#" class="comment_user">' +
            comment['author'] + '</a></li>' +
            '<li><span class="comment_time">' +
            comment['timestamp'] + '</span></li>' +
            '<li class="f_r"><a href="javascript:;" onclick="isComFavorite(this)"><i class="iconfont ' +
            comment['isFav'] + '"></i><span>(' +  comment['up_num'] +
            ')</span></a></li><li class="f_r"><a href="javascript:;" class="reply_btn">' +
            '<i class="iconfont icon-icon_huifu-xian huifu"></i></a></li>' +
            '</ul><div class="comment_content">' + comment['content_html'] +
            '</div><span comid="' + comment['id'] +
            '" articleid="' +comment['article_id'] +'"></span>';
        // 主评论加一个外层div
        if (!comment['parent_id']) {
             comment_str =  '<div class="max_content">' + comment_str;
        };
        if (comment['children']) {
            comment_str += makeCommentTree(comment['children']);
        }
        comment_str += '</div>';
        if (!comment['parent_id']) {
             comment_str = comment_str + '</div>';
        };
        htmls += comment_str;
    });

    return htmls;
};

// ajax GET请求评论数据
function ajax_comments() {
    var article_id = $('#comment_box').attr('a_id');
    var url = '/article/' + article_id + '/comments';
    $.get(url, function (res) {
        if (res.errno === '0') {
            html_str = makeCommentTree(res.data);
            $('#comment_box').html(html_str);

            $('.reply_btn').click(function () {
                $('.reply_textarea').parents('.max_content').css('max-height', '170px');
                $('.reply_textarea').remove();
                $(this).closest('ul').next().after(
                    '<div class="reply_textarea"><textarea class="com_text" name="cli_content"></textarea>' +
                    '<input type="botton" class="com_btn" onclick="bot_com(this)" style="width: 28px;" value="评论"></div>'
                );
                $('.com_text').focus();

                // 回复评论时，完全显示评论和表单
                var com_box_obj = $('.reply_textarea').parents('.max_content').children();
                $('.reply_textarea').parents('.max_content').css('max-height', com_box_obj.outerHeight(true));
                if ($('.reply_textarea').parents('.max_content').next().prop('tagName') == 'BOTTON') {
                    $('.reply_textarea').parents('.max_content').next().text('收起评论');
                };
            });

            // 展开 收起评论条件判断
            var com_boxes = $('.max_content').children();
            for (var i=0;i<com_boxes.length;i++) {
                com_box = $(com_boxes[i]);
                if(com_box.height() > 170) {
                    com_box.parent().after('<botton onclick="expand_com(this)" class="expand_btn com_btn">展开评论</botton>')
                };
            };

        }
    }, 'json');
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
    var com_content = thisobj.prev().val();
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
});

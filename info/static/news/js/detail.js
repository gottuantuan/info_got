function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}


$(function(){

    // 打开登录框
    $('.comment_form_logout').click(function () {
        $('.login_form_con').show();

    })


    // 收藏
    $(".collection").click(function () {
        var params = {
            'news_id':$(this).attr('data-newid'),
            'action':'collect'
        }
       $.ajax({
           url:'/news_collect',
           type:'post',
           contentType:'application/json',
           data:JSON.stringify(params),
           headers:{
               'X-CSRFToken':getCookie('csrf_token')
           },
           success:function (resp) {
               if(resp.errno=='0'){
                   $('.collection').hide();
                   $('.collected').show();
               }else if(resp.errno=='4101'){
                   $('.login_form_con').show();

               }else{
                   alert(resp.errmsg);
               }
           }
       })
    })

    // 取消收藏
    $(".collected").click(function () {

      var params = {
            'news_id':$(this).attr('data-newid'),
            'action':'collect'
        }
       $.ajax({
           url:'/news_collect',
           type:'post',
           contentType:'application/json',
           data:JSON.stringify(params),
           headers:{
               'X-CSRFToken':getCookie('csrf_token')
           },
           success:function (resp) {
               if(resp.errno=='0'){
                   $('.collection').show();
                   $('.collected').hide();
               }else if(resp.errno=='4101'){
                   $('.login_form_con').show();

               }else{
                   alert(resp.errmsg);
               }
           }
       })
    })

        // 评论提交
    $(".comment_form").submit(function (e) {
        e.preventDefault();

    })

    $('.comment_list_con').delegate('a,input','click',function(){

        var sHandler = $(this).prop('class');

        if(sHandler.indexOf('comment_reply')>=0)
        {
            $(this).next().toggle();
        }

        if(sHandler.indexOf('reply_cancel')>=0)
        {
            $(this).parent().toggle();
        }

        if(sHandler.indexOf('comment_up')>=0)
        {
            var $this = $(this);
            if(sHandler.indexOf('has_comment_up')>=0)
            {
                // 如果当前该评论已经是点赞状态，再次点击会进行到此代码块内，代表要取消点赞
                $this.removeClass('has_comment_up')
            }else {
                $this.addClass('has_comment_up')
            }
        }

        if(sHandler.indexOf('reply_sub')>=0)
        {
            alert('回复评论')
        }
    })

       // 关注当前新闻作者
    $(".focus").click(function () {
        var user_id = $(this).attr('data-userid')
        var params = {
            "action": "follow",
            "user_id": user_id
        }
        $.ajax({
            url: "/followed_user",
            type: "post",
            contentType: "application/json",
            headers: {
                "X-CSRFToken": getCookie("csrf_token")
            },
            data: JSON.stringify(params),
            success: function (resp) {
                if (resp.errno == "0") {
                    // 关注成功
                    var count = parseInt($(".follows b").html());
                    count++;
                    $(".follows b").html(count + "")
                    $(".focus").hide()
                    $(".focused").show()
                }else if (resp.errno == "4101"){
                    // 未登录，弹出登录框
                    $('.login_form_con').show();
                }else {
                    // 关注失败
                    alert(resp.errmsg)
                }
            }
        })
    })

    // 取消关注当前新闻作者
    $(".focused").click(function () {
        var user_id = $(this).attr('data-userid')
        var params = {
            "action": "unfollow",
            "user_id": user_id
        }
        $.ajax({
            url: "/followed_user",
            type: "post",
            contentType: "application/json",
            headers: {
                "X-CSRFToken": getCookie("csrf_token")
            },
            data: JSON.stringify(params),
            success: function (resp) {
                if (resp.errno == "0") {
                    // 取消关注成功
                    var count = parseInt($(".follows b").html());
                    count--;
                    $(".follows b").html(count + "")
                    $(".focus").show()
                    $(".focused").hide()
                }else if (resp.errno == "4101"){
                    // 未登录，弹出登录框
                    $('.login_form_con').show();
                }else {
                    // 取消关注失败
                    alert(resp.errmsg)
                }
            }
        })

    })

})


function updateCommentCount(){
    var count = $('.comment_list').length
    $('.comment_count').html(count+"条评论")
}
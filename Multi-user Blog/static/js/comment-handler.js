// Comment Handlers
// Edit Handler
function postComment(THIS,blog_id){
	var $title = $("#new-comment-form input[name=title]").val();
	var $content = $("#new-comment-form textarea[name=texts]").val();
	// Check if submitting title and contents are non-empty.
	if(!($title.length > 0 && $content.length>0)){
		$("#comments div.header div.result").html("Invalid. Title and content must not be empty.");
		return false;
	};
	// If all is well, send data to server.
	$.ajax({
		url: "/blog/"+blog_id+"/comment/new",
		type: "POST",
		contentType:"application/json",
		dataType: 'json',
		data: JSON.stringify({"title": $title, "content":$content}),
		processData: false,
		success: function(result){
			console.log(result)
			if(result["success"]){
				$("#comments div.header div.result").html("Comment has been added successfully.");
				// Clear texts in the form
				$("#new-comment-form input").val("");
				$("#new-comment-form textarea").val("");
				// Append new comment in the list of comments
				var $count = localStorage.count;
				$("#comments ul").prepend("<li id='new-comment-"+$count+"' class='comment'><div class='content'><h3 class='title'>"+result["title"]+"</h3><div class='meta'><span class='author'>"+result["author"]+"</span><span class='date-created'>"+result["date_created"]+"</span></div><pre class='texts'>"+result["content"]+"</pre><div class='options'><button class='edit'>Edit</button><button class='delete'>Delete</button></div><input type='hidden' value='"+result["id"]+"'></div><div class='result'></div></li>");
				$(".comment button.edit").click(function(){render_comment_edit(this);});
				$(".comment button.delete").click(function(){delete_comment(this);});
			};
		}, 
		error: function(error){
			console.log(error)
			if(error["status"] == 400){
				$("#comments div.header div.result").html("Title and comment must not be empty.");
			} else if(error["status"] == 401) {
				$("#comments div.header div.result").html("User must be logged in to post this comment.");
			} else if(error["status"] == 404){
				window.location.href = "/blog/not_found";
			};
		}
	});
};

function renderCommentEdit(THIS,blog_id){
	var $li_id = $(THIS).closest("li").prop("id");
	var $title = $('#'+$li_id+" h3.title").html();
	var $content = $('#'+$li_id+" div.texts").html();
	var $comment_key_id = $("#"+$li_id+" input[type=hidden]").val();
	// Validate user
	var $url = "/blog/"+blog_id+"/comment/validate?id="+$comment_key_id;
	$.ajax({
		url: $url,
		type: "GET",
		success:function(result){
			if(result["success"]){
				var $form = "<div class='edit'><form action=''><div class='form-group'><input type='text' placeholder='title' name='title' value='"+$title+"'></div><div class='form-group'><textarea name='texts' placeholder='Write your comments here.'>"+$content+"</textarea></div></form><button class='submit'>Submit</button></div>";
				$("#"+$li_id+" div.content").css("display","None");
				$("#"+$li_id+" div.content").after($form);
				$(".comment button.submit").click(function(){
					submit_comment_edit(this);
				});  
	 		};
		},
		error:function(error){
			if(error["status"] == 401){
				$("#"+$li_id+" div.result").html("Invalid. Either user is not signed in, or is not the author of this comment.");
			} else {
				console.log(error);
			};
		}  
	});
};

function submitCommentEdit(THIS,blog_id){
	var $error_400 = "Invalid. Both title and content must not be empty.";
	// Harvest form data.
	var $li_id = $(THIS).closest("li").prop("id");
	var $comment_key_id = $("#"+$li_id+" input[type=hidden]").val();
	var $new_title = $("#"+$li_id+" input[name=title]").val();
	var $new_content = $("#"+$li_id+" textarea[name=texts]").val();
	// Check if submitting title and contents are non-empty.
	if(!($new_title.length > 0 && $new_content.length>0)){
		$("#"+$li_id+" div.result").html($error_400);
		return false;
	};
	console.log({"title": $new_title, "content":$new_content, "id":$comment_key_id});
	// If all is well, send data to server.
	$.ajax({
		url:"/blog/"+blog_id+"/comment/edit",
		type: "PUT",
		contentType:"application/json",
		dataType: 'json',
		data: JSON.stringify({"title": $new_title, "content":$new_content, "id":$comment_key_id}),
		processData: false,
		success: function(result){
			if(result["success"]){
				console.log("This comment has been edited successfully.");
				// Replace the comment with new title and content.
				$("#"+$li_id+" h3.title").html($new_title);
				$("#"+$li_id+" div.texts").html($new_content);
				// Remove form and re-display content.
				$("#"+$li_id+" div.content").css("display","initial");
				$("#"+$li_id+" div.edit").remove();
			};
		}, 
		error: function(error){
			if(error["status"] == 400){
				$("#"+$li_id+" div.result").html($error_400);
			} else if(error["status"] == 401) {
				window.location.href = "/blog/not_authorized";
			} else if(error["status"] == 404){
				window.location.href = "/blog/not_found";
			};
		}
	});
}; 

function deleteComment(THIS,blog_id){
	// Harvest comment id.
	var $li_id = $(THIS).closest("li").prop("id");
	var $comment_key_id = $("#"+$li_id+" input[type=hidden]").val();		
	// Send AJAX DELETE request to server.
	$.ajax({
		url: "/blog/"+blog_id+"/comment/delete?id="+$comment_key_id,
		type: "DELETE",
		dataType:'json',
		success:function(result){
			if(result["success"]){
				$("#"+$li_id).remove();
			}
		},
		error:function(error){
			if(error["status"]==400){
				console.log(400);
				$("#"+$li_id+" div.result").html("Invalid. Comment is not found.");
			} else if(error["status"]==401){
				console.log(401);
				$("#"+$li_id+" div.result").html("Invalid. User is not logged in.");
			} else if(error["status"]==403){
				console.log(403);
				$("#"+$li_id+" div.result").html("Not allowed. User must be the author of this post.");
			} else if(error["status"]==404){
				window.location.href="/blog/not_found";
			}
		}

	});

};
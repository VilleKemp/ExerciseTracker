/**** START CONSTANTS****/

/** 
 * Set this to true to activate the debugging messages. 
 * @constant {boolean}
 * @default 
 */
var DEBUG = true;

/** 
 * Mason+JSON mime-type 
 * @constant {string}
 * @default 
 */
const MASONJSON = "application/vnd.mason+json";

const PLAINJSON = "application/json";

/** 
 * Link to Users_profile
 * @constant {string}
 * @default 
 */
const FORUM_USER_PROFILE = "/profiles/users";

/** 
 * Default datatype to be used when processing data coming from the server.
 * Due to JQuery limitations we should use json in order to process Mason responses
 * @constant {string}
 * @default 
 */
const DEFAULT_DATATYPE = "json";

/** 
 * Entry point of the application
 * @constant {string}
 * @default 
 */
const ENTRYPOINT = "/exercisetracker/api/users/"; //Entrypoint: Resource Users

/**** END CONSTANTS****/


/**** START RESTFUL CLIENT****/
/**** OWN IMPLEMENTATION****/
/****
Modifies exercise from data get from the form.
->Sends API call of PUT  to Exercise resorouce inorder to modify it in the database 
<-Returns 200 if OK
****/


function modify_exercise(apiurl,exercise){
    var userData = JSON.stringify(exercise);
    return $.ajax({
        url: apiurl,
        type: "PUT",
        dataType:DEFAULT_DATATYPE,
        data:userData,
        contentType: PLAINJSON
    }).done(function (data, textStatus, jqXHR){
        if (DEBUG) {
            console.log ("RECEIVED RESPONSE: data:",data,"; textStatus:",textStatus);
        }
        alert ("Exercise modified");
        //empty and hide
        $("#modify_exercise_form").children('div[class=form_content]').empty();
        $("#modify_exercise").hide();
        //refresh user info       
        get_exercise(apiurl);
		get_user($("#remove_user_button").attr('href'));
        $("#userData").show();        
    })
    
}
/****
Gets all users from database.
->Sends GET API call to Users resource inorder ot get all users.
<-Returns 200 and Users if succesful
****/
function getUsers(apiurl) {
    apiurl = apiurl || ENTRYPOINT;
    $("#mainContent").hide();
    return $.ajax({
        url: apiurl,
        dataType:DEFAULT_DATATYPE,
		contentType: 'application/json'
    }).always(function(){
        //Remove old list of users
        //clear the form data hide the content information(no selected)
        $("#user_list").empty();
        $("#mainContent").hide();

    }).done(function (data, textStatus, jqXHR){
        if (DEBUG) {
            console.log ("RECEIVED RESPONSE: data:",data,"; textStatus:",textStatus);
        }
		console.log ("RECEIVED RESPONSE: data:",data,"; textStatus:",textStatus);
        //Extract the users
        users = data.items;

        for (var i=0; i < users.length; i++){
            var user = users[i];
            //Extract the username by getting the data values. Once obtained
            // the username use the method appendUserToList to show the user
            // information in the UI.
            appendUserToList(user["@controls"].self.href, user.username);
        }


        
    }).fail(function (jqXHR, textStatus, errorThrown){
        if (DEBUG) {
            console.log ("RECEIVED ERROR: textStatus:",textStatus, ";error:",errorThrown);
        }
        //Inform user about the error using an alert message.
        alert ("Could not fetch the list of users.  Please, try again");
    });
}
/****
Gets all  friends of the userfrom database.
->Sends GET API call to Friends resource inorder to get all users.
<-Returns 200 and Users if succesful
****/
function getUsersFriends(apiurl, friendname) {
    apiurl = apiurl || ENTRYPOINT;
    return $.ajax({
        url: apiurl,
        dataType:DEFAULT_DATATYPE,
        contentType: 'application/json'
    }).always(function(){
        //Remove old list of users
        //clear the form data hide the content information(no selected)
        $("#friend_list").empty();
		$("#remove_friend_list").empty();

    }).done(function (data, textStatus, jqXHR){
        if (DEBUG) {
            console.log ("RECEIVED RESPONSE: data:",data,"; textStatus:",textStatus);
        }
        console.log ("RECEIVED RESPONSE: data:",data,"; textStatus:",textStatus);
        //Extract the users
        friends = data.items;

        for (var i=0; i < friends.length; i++){
            var friend = friends[i];
            //Extract the username by getting the data values. Once obtained
            // the username use the method appendUserToList to show the user
            // information in the UI.
            var friend_links = friend["@controls"];
			console.log(friend_links);
            var remove_link = friend_links["remove-friend"].href;
            console.log("HREF: " + friend["@controls"].self.href + " Friendname:" + friend.friend);
			console.log("HREF Remove: " + friend_links["remove-friend"].href + " Friendname:" + friend.friend);
            appendFriendToList(friend["@controls"].self.href,friend.friend,friend_links["remove-friend"].href);
        }
        
    }).fail(function (jqXHR, textStatus, errorThrown){
        if (DEBUG) {
            console.log ("RECEIVED ERROR: textStatus:",textStatus, ";error:",errorThrown, "URL: apiurl:", apiurl);
                    }
        //Inform user about the error using an alert message.
        //alert ("Could not fetch the list of friends.  Please, try again");
    });
}
/****
Removes specified user from database.
->Sends Remove API call to Users resource inorder to delete it.
<-Returns 200 if User was deleted sucessfully. 
****/
function remove_user(apiurl){
	return $.ajax({
		url: apiurl, //The URL of the resource
		type: "DELETE", //The resource method
        dataType:DEFAULT_DATATYPE,
		contentType: 'application/json'
    }).done(function (data, textStatus, jqXHR){

		//hides exercise information. migth be smarter to empty?
		$("#userData").hide();
		$("#exercise_list").empty();
		getUsers();
		
	});		
}
/****
Removes specified exercise from database.
->Sends Remove API call to Exercise resource inorder to delete. it
<-Returns 200 if User was deleted sucessfully. 
****/
function remove_exercise(apiurl){
	return $.ajax({
		url: apiurl, //The URL of the resource
		type: "DELETE", //The resource method
        dataType:DEFAULT_DATATYPE,
		contentType: 'application/json'
    }).done(function (data, textStatus, jqXHR){
		//refresh the exercise list
		var username = $("#username").val();
		username = username.replace("Username: ", "");
		
		console.log(username);
		getUsersExercises("/exercisetracker/api/exercises/", username);
		//hides exercise information. migth be smarter to empty?
		$("#exerciseData").hide();
		
	});		
}
/****
Startup function that initializes the website and nessecary setup.
****/
function startup(apiurl) {
    apiurl = apiurl || ENTRYPOINT;
    $("#mainContent").hide();
	$("#hideAllUsersButtonContainer").hide();
    return $.ajax({
        url: apiurl,
        dataType:DEFAULT_DATATYPE,
		contentType: 'application/json'
    }).always(function(){
        //Remove old list of users
        //clear the form data hide the content information(no selected)
        $("#user_list").empty();
        $("#mainContent").hide();

    }).done(function (data, textStatus, jqXHR){
        if (DEBUG) {
            console.log ("RECEIVED RESPONSE: data:",data,"; textStatus:",textStatus);
        }
		console.log ("RECEIVED RESPONSE: data:",data,"; textStatus:",textStatus);
        //Extract the users
        users = data.items;
          //Prepare the new_user_form to create a new user
        var create_ctrl = data["@controls"]["add user"]
        console.log(create_ctrl.schemaUrl);
        if (create_ctrl.schema) {
            createFormFromSchema(create_ctrl.href, create_ctrl.schemaUrl, "new_user_form");
        }
        else if (create_ctrl.schemaUrl) {
            $.ajax({
                url: create_ctrl.schemaUrl,
                dataType: DEFAULT_DATATYPE
            }).done(function (data, textStatus, jqXHR) {

                createFormFromSchema(create_ctrl.href, data, "new_user_form");
				
            }).fail(function (jqXHR, textStatus, errorThrown) {
                if (DEBUG) {
                    console.log ("RECEIVED ERROR: textStatus:",textStatus, ";error:",errorThrown);
                }
                alert ("Could not fetch form schema.  Please, try again");
            });
        }
        //getUsers(apiurl)
    }).fail(function (jqXHR, textStatus, errorThrown){
        if (DEBUG) {
            console.log ("RECEIVED ERROR: textStatus:",textStatus, ";error:",errorThrown);
        }
        //Inform user about the error using an alert message.
        alert ("Could not fetch the list of users.  Please, try again");
    });
}
/****
Gets all exercises of the user
->Sends Get API call to Exercises resource inorder to find them.
<-Returns 200 and Exercises if found. 
****/
function getUsersExercises(apiurl, username) {
    apiurl = apiurl || ENTRYPOINT;
    return $.ajax({
        url: apiurl,
        dataType:DEFAULT_DATATYPE,
		contentType: 'application/json'
    }).always(function(){
        //Remove old list of users
        //clear the form data hide the content information(no selected)
        $("#exercise_list").empty();

    }).done(function (data, textStatus, jqXHR){
        if (DEBUG) {
            console.log ("RECEIVED RESPONSE: data:",data,"; textStatus:",textStatus);
        }
		console.log ("RECEIVED RESPONSE: data:",data,"; textStatus:",textStatus);
        //Extract the users
        exercises = data.items;
        for (var i=0; i < exercises.length; i++){
            var exercise = exercises[i];
			
			if(exercise.username == username)
			{
            //Extract the username by getting the data values. Once obtained
            // the username use the method appendUserToList to show the user
            // information in the UI.
		    type = exercise.type
            exercise.type = exercise.type.charAt(0).toUpperCase() + exercise.type.slice(1)
            appendExerciseToList(exercise["@controls"].self.href, exercise.type, exercise.date)
			}
    }});
}
/****
Modifies specified user in the database.
->Sends Put API call to User resource inorder to modify it.
<-Returns 200 if User was modified sucessfully. 
****/
function modify_user(apiurl,user){
    var userData = JSON.stringify(user);
    return $.ajax({
        url: apiurl,
        type: "PUT",
        dataType:DEFAULT_DATATYPE,
        data:userData,
        contentType: PLAINJSON
    }).done(function (data, textStatus, jqXHR){
        if (DEBUG) {
            console.log ("RECEIVED RESPONSE: data:",data,"; textStatus:",textStatus);
        }
        alert ("User modified");
        //empty and hide
        $("#modify_user_form").children('div[class=form_content]').empty();
        $("#modify_user").hide();
        //refresh user info

        get_user(apiurl); 
        $("#userData").show();        
    })
    
}

/****
Adds specified exercise into  the database.
->Sends Post API call to Exercises resource inorder to add to it.
<-Returns 200 if Exercise was added sucessfully. 
****/
function add_exercise(apiurl,exercise){
    var exerciseData = JSON.stringify(exercise);
    return $.ajax({
        url: apiurl,
        type: "POST",
        dataType:DEFAULT_DATATYPE,
        data:exerciseData,
        contentType: PLAINJSON
    }).done(function (data, textStatus, jqXHR){
        if (DEBUG) {
            console.log ("RECEIVED RESPONSE: data:",data,"; textStatus:",textStatus);
        }
        alert ("Exercise successfully added");
        //empty and hide the add_exercise form
        $("#form_content").empty();
        $("#add_exercise").hide();
        //refresh the exercise list
        getUsersExercises("/exercisetracker/api/exercises/", data.username); 
    }).fail(function (jqXHR, textStatus, errorThrown){
        if (DEBUG) {
            console.log ("RECEIVED ERROR: textStatus:",textStatus, ";error:",errorThrown);
        }
        alert ("Could not create new exercise:"+jqXHR.responseJSON.message);
    });    
    
    
}
/****
Adds specific user in to the database.
->Sends Post API call to User resource inorder to add to it.
<-Returns 200 if User was added sucessfully. 
****/
function add_user(apiurl,user){
    var userData = JSON.stringify(user);
    var username = user.username;
    return $.ajax({
        url: apiurl,
        type: "POST",
        dataType:DEFAULT_DATATYPE,
        data:userData,
        contentType: PLAINJSON
    }).done(function (data, textStatus, jqXHR){
        if (DEBUG) {
            console.log ("RECEIVED RESPONSE: data:",data,"; textStatus:",textStatus);
        }
        alert ("User successfully added");
		
		get_user(data["@controls"].self.href);

		$("#newUser").hide();
		$("#userData").show();
		prepareUserDataVisualization();
		$("#modify_exercise").hide();

		

    }).fail(function (jqXHR, textStatus, errorThrown){
        if (DEBUG) {
            console.log ("RECEIVED ERROR: textStatus:",textStatus, ";error:",errorThrown);
        }
        alert ("Could not create new user:"+jqXHR.responseJSON.message);
    });
}

/****
Gets specific user in the database.
->Sends Get API call to User resource inorder to get it.
<-Returns 200 and User if found. 
****/
function get_user(apiurl) {
    return $.ajax({
		url: apiurl,
        dataType:DEFAULT_DATATYPE,
		contentType: 'application/json'
    }).done(function (data, textStatus, jqXHR){
        if (DEBUG) {
            console.log ("RECEIVED RESPONSE: data:",data,"; textStatus:",textStatus);
        }


        //hide
		$("#modify_exercise").hide();
        

		//save user info for later use
		var info= data;
		
        $("#username").val("Username: " + data.username);
		$("#visibility").val("Visibility: " + data.visibility || "??");
		$("#description").val("Description: " + data.description || "??");
		$("#password").val(data.password || "??");
		$("#avatar").val("Avatar: " +data.avatar || "??");
        
        //Extract user information
        var user_links = data["@controls"];
		console.log("#userlinks");
		console.log(user_links);
		
		if("delete user information" in user_links)
		{
		$("#remove_user_button").attr("href",user_links["delete user information"].href);	
			
		}
		
		if("modify-user" in user_links)
		{
        $("#modifyUser").attr("href",user_links["modify-user"].href);
		}
		
        if("list-friends" in user_links)
        {
            var friends_url = user_links["list-friends"].href;
        }
        if("add-friend" in user_links)
        {
            var my_friend_url = user_links["add-friend"].href;
            console.log(user_links["add-friend"].href);
        }
		if (my_friend_url ){
            $("#add_friend_href").attr("href", user_links["add-friend"].href);

        }

		//generate modify user form
		//TEMPORARY FIX UNTIL THE DATA STRUCTURE HAS BEEN FIXED
		var schema = user_links["modify-user"].schemaUrl;
		schema = "/forum/schema/user/";
		$.ajax({
                url: schema,
                dataType: DEFAULT_DATATYPE
            }).done(function (data, textStatus, jqXHR) {
                console.log("modify user form creation success");
				console.log(data);

                createFormFromSchema(user_links["modify-user"].href, data, "modify_user_form");
			//fill the form
			console.log("right before fill");
		
			$("#modify_user").children().children('div[class="form_content"]').children('input[name="username"]').val(info.username);
			$("#modify_user").children().children('div[class="form_content"]').children('input[name="password"]').val(info.password);
			$("#modify_user").children().children('div[class="form_content"]').children('input[name="description"]').val(info.description);
			$("#modify_user").children().children('div[class="form_content"]').children('input[name="avatar"]').val(info.avatar);
			$("#modify_user").children().children('div[class="form_content"]').children('input[name="visibility"]').val(info.visibility);
                
			
			//hide the form
			$("#modify_user").hide();
			
			
            })

       getUsersExercises("/exercisetracker/api/exercises/", data.username)
       getUsersFriends(friends_url, data.username)



    }).fail(function (jqXHR, textStatus, errorThrown){
        if (DEBUG) {
            console.log ("RECEIVED ERROR: textStatus:",textStatus, ";error:",errorThrown);
        }
        //Show an alert informing that I cannot get info from the user.
        alert ("Cannot extract information about this user");
        //Deselect the user from the list.
        deselectUser();
    });
	
	
}
/****
Gets specific exercise from the database.
->Sends Get API call to Exercise resource inorder to get it.
<-Returns 200 and exercise if found.
After that adds and shows found information to UI  
****/
function get_exercise(apiurl) {
    return $.ajax({
        url: apiurl,
        dataType:DEFAULT_DATATYPE,
        contentType: 'application/json'
    }).done(function (data, textStatus, jqXHR){
        if (DEBUG) {
            console.log ("RECEIVED RESPONSE: data:",data,"; textStatus:",textStatus);
        }

		//make sure exercise data is shown
		$("#exerciseData").show();
		$("#modify_exercise").hide();

        //Fill basic information from the user_basic_form
        $("#exerciseid").val(data.exerciseid);   
        $("#type").val("Type: " + data.type);
        $("#value").val("Value: " + data.value || "??");
        $("#valueunit").val("Valueunit: " + data.valueunit || "??");
        $("#date").val("Date: "  + data.date || "??");
        $("#time").val("Time: " +data.time || "??");
        $("#timeunit").val("Timeunit: " +data.timeunit || "??");
        
        //Extract user information
        var exercise_links = data["@controls"];
        console.log(exercise_links);
        
        if("remove-exercise" in exercise_links){
           console.log(exercise_links["remove-exercise"].href);
		   //set remove exercise buttons href
		   $("#remove_exercise_button").attr("href",exercise_links["remove-exercise"].href);
            
        }
        
        if("modify-exercise"in exercise_links){
           $("#modify_exercise_button").attr("href",exercise_links["modify-exercise"].href);
           
        }
        //create modify form
        schemaurl= exercise_links["modify-exercise"].schemaUrl;
        //TEMPORARY FIX REMOVE LATER
        schemaurl=schemaurl.replace("exercisetracker","forum");
        $.ajax({
                url: schemaurl,
                dataType: DEFAULT_DATATYPE
            }).done(function (info, textStatus, jqXHR) {
                
                createFormFromSchema(exercise_links["modify-exercise"].href, info, "modify_exercise_form");
                //fill the form
                $("#modify_exercise_form").children("div[class=form_content]").children("input[name=username]").val(data.username);
                $("#modify_exercise_form").children("div[class=form_content]").children("input[name=type]").val(data.type);
                $("#modify_exercise_form").children("div[class=form_content]").children("input[name=value]").val(data.value);
                $("#modify_exercise_form").children("div[class=form_content]").children("input[name=valueunit]").val(data.valueunit);
                $("#modify_exercise_form").children("div[class=form_content]").children("input[name=date]").val(data.date);
                $("#modify_exercise_form").children("div[class=form_content]").children("input[name=time]").val(data.time);
                $("#modify_exercise_form").children("div[class=form_content]").children("input[name=timeunit]").val(data.timeunit);

            }) 

            
    }).fail(function (jqXHR, textStatus, errorThrown){
        if (DEBUG) {
            console.log ("RECEIVED ERROR: textStatus:",textStatus, ";error:",errorThrown);
        }
        //Show an alert informing that I cannot get info from the user.
        alert ("Cannot extract information about this exercise");


    });

}
/****
Adds specified friend to a user
->Sends post API call to Friends resource inorder to add to it.
<-Returns 200 if friend was added sucessfully. 
****/
function add_friend(apiurl,username, friendname){
    
    var name = username;// $("#userHeader").children('input[name="username"]').val();

    name = name.replace("Username: ", "");
    var Data = {"username":name, "friendname":friendname};
    var userData = JSON.stringify(Data);
	console.log ("RECEIVED URL: url:",apiurl, "; Received DATA:", userData);
    return $.ajax({
        url: apiurl,
        type: "POST",
        dataType:DEFAULT_DATATYPE,
        data:userData,
        contentType: PLAINJSON
    }).done(function (data, textStatus, jqXHR){
        if (DEBUG) {
            console.log ("RECEIVEEED RESPONSE: data:",data,"; textStatus:",textStatus);
        }
        getUsersFriends(apiurl)
        alert ("Friend successfully added");
    }).fail(function (jqXHR, textStatus, errorThrown){
        if (DEBUG) {
            console.log ("RECEIVED ERROR: textStatus:",textStatus, ";error:",errorThrown);
        }
        alert ("Could not create new user:"+jqXHR.responseJSON.message);
    });
}

/****
Removes specified friend from the database.
->Sends remove API call to Friends resource inorder to remove from it.
<-Returns 200 if friend was deleted sucessfully. 
****/
function remove_friend(apiurl,username, friendname){
    
    var name = username;// $("#userHeader").children('input[name="username"]').val();

    name = name.replace("Username: ", "");
    var Data = {"username":name, "friendname":friendname};
    var userData = JSON.stringify(Data);
    console.log ("RECEIVED URL: url:",apiurl, "; Received DATA:", userData);
    return $.ajax({
        url: apiurl, //The URL of the resource
        type: "DELETE", //The resource method
        dataType:DEFAULT_DATATYPE,
        data:userData,
        contentType: 'application/json'
    }).done(function (data, textStatus, jqXHR){
        if (DEBUG) {
            console.log ("RECEIVEED RESPONSE: data:",data,"; textStatus:",textStatus);
        }
        getUsersFriends(apiurl)
        alert ("Friend successfully deleted");
    }).fail(function (jqXHR, textStatus, errorThrown){
        if (DEBUG) {
            console.log ("RECEIVED ERROR: textStatus:",textStatus, ";error:",errorThrown);
        }
        alert ("Could not delete friend:"+jqXHR.responseJSON.message);
    });
}
   
/**** END RESTFUL CLIENT****/

/**** UI HELPERS ****/

function appendUserToList(url, username) {
    var $user = $('<li>').html('<a class= "user_link" href="'+url+'">'+username+'</a>');
    //Add to the user list
    $("#user_list").append($user);
    return $user;
}
function appendFriendToList(url, friendname, removeurl) {
    var $friend = $('<li>').html('<a class= "user_link" href="'+url+'">'+friendname+'</a>');
    var $removefriend = $('<li>').html('<a id= '+ friendname +' class= "user_link" href="'+removeurl+'">'+"Remove"+'</a>');
    //Add to the user list
    $("#friend_list").append($friend);
    $("#remove_friend_list").append($removefriend);
    return $friend;
}

function appendExerciseToList(url, type, date) {
    var $exercise = $('<li>').html('<a class= "exercise_link" href="'+url+'">'+type+ " " + date +'</a>');
    //Add to the user list
    $("#exercise_list").append($exercise);
    return $exercise;

}


/*** Functions that were in the original forum exercise***/
/**
 * Populate a form with the <input> elements contained in the <i>schema</i> input parameter.
 * The action attribute is filled in with the <i>url</i> parameter. Values are filled
 * with the default values contained in the template. It also marks inputs with required property. 
 *
 * @param {string} url - The url of to be added in the action attribute
 * @param {Object} schema - a JSON schema object ({@link http://json-schema.org/}) 
 * which is utlized to append <input> elements in the form
 * @param {string} id - The id of the form is gonna be populated
**/
function createFormFromSchema(url,schema,id){
    $form=$('#'+ id);
    $form.attr("action",url);
    //Clean the forms
    $form_content=$(".form_content",$form);
    $form_content.empty();
    $("input[type='button']",$form).hide();
    
    if (schema.properties) {
        var props = schema.properties;
        
        Object.keys(props).forEach(function(key, index) {
            if (props[key].type == "object") {
               
                appendObjectFormFields($form_content, key, props[key]);
            }
            else {
                appendInputFormField($form_content, key, props[key], schema.required.includes(key));
            }
            
        });
    }
    
    return $form;
}
/**
 * Private class used by {@link #createFormFromSchema}
 *
 * @param {jQuery} container - The form container
 * @param {string} The name of the input field
 * @param {Object} object_schema - a JSON schema object ({@link http://json-schema.org/}) 
 * which is utlized to append properties of the input
 * @param {boolean} required- If it is a mandatory field or not.
**/
function appendInputFormField($container, name, object_schema, required) {
    var input_id = name;
    var prompt = object_schema.title;
    var desc = object_schema.description;
    
    $input = $('<input type="text"></input>');
    $input.addClass("editable");
    $input.attr('name',name);
    $input.attr('id',input_id);
    $label_for = $('<label></label>');
    $label_for.attr("for",input_id);
    $label_for.text(prompt);
    $container.append($label_for);
    $container.append($input);
    
    if(desc){
        $input.attr('placeholder', desc);
    }
    if(required){
        $input.prop('required',true);
        $label = $("label[for='"+$input.attr('id')+"']");
        $label.append(document.createTextNode("*"));
    }    
}
/**
 * Private class used by {@link #createFormFromSchema}. Appends a subform to append
 * input
 *
 * @param {jQuery} $container - The form container
 * @param {string} The name of the input field
 * @param {Object} object_schema - a JSON schema object ({@link http://json-schema.org/}) 
 * which is utlized to append properties of the input
 * @param {boolean} required- If it is a mandatory field or not.
**/
function appendObjectFormFields($container, name, object_schema) {
    $div = $('<div class="subform"></div>');
    $div.attr("id", name);
    Object.keys(object_schema.properties).forEach(function(key, index) {
        if (object_schema.properties[key].type == "object") {
            // only one nested level allowed
            // therefore do nothing            
        }
        else {
            appendInputFormField($div, key, object_schema.properties[key], false);
        }
    });
    $container.append($div);
}

/**
 * Populate a form with the content in the param <i>data</i>.
 * Each data parameter is going to fill one <input> field. The name of each parameter
 * is the <input> name attribute while the parameter value attribute represents 
 * the <input> value. All parameters are by default assigned as 
 * <i>readonly</i>.
 * 
 * NOTE: All buttons in the form are hidden. After executing this method adequate
 *       buttons should be shown using $(#button_name).show()
 *
 * @param {jQuery} $form - The form to be filled in
 * @param {Object} data - An associative array formatted using Mason format ({@link https://tools.ietf.org/html/draft-kelly-json-hal-07})
**/

function fillFormWithMasonData($form, data) {
    
    console.log(data);
    
    $(".form_content", $form).children("input").each(function() {
        if (data[this.id]) {
            $(this).attr("value", data[this.id]);
        }
    });
    
    $(".form_content", $form).children(".subform").children("input").each(function() {
        var parent = $(this).parent()[0];
        if (data[parent.id][this.id]) {
            $(this).attr("value", data[parent.id][this.id]);
        }
    });
}

/**
 * Serialize the input values from a given form (jQuery instance) into a
 * JSON document.
 * 
 * @param {Object} $form - a jQuery instance of the form to be serailized
 * @returs {Object} An associative array in which each form <input> is converted
 * into an element in the dictionary. 
**/
function serializeFormTemplate($form){
    var envelope={};
    // get all the inputs into an array.
    var $inputs = $form.find(".form_content input");
    $inputs.each(function() {
        envelope[this.id] = $(this).val();
    });
    
    var subforms = $form.find(".form_content .subform");
    subforms.each(function() {
        
        var data = {}
        
        $(this).children("input").each(function() {
            data[this.id] = $(this).val();
        });
        
        envelope[this.id] = data
    });
    return envelope;
}


/**
 * Helper method to be called before showing new user data information
 * It purges old user's data and hide all buttons in the user's forms (all forms
 * elements inside teh #userData)
 *
**/
function prepareUserDataVisualization() {
    
    //Remove all children from form_content
    $("#userData .form_content").empty();
    //Hide buttons
    $("#userData .commands input[type='button'").hide();
    //Reset all input in userData
    $("#userData input[type='text']").val("??");
    //Remove old messages
    $("#messages_list").empty();
    //Be sure that the newUser form is hidden
    $("#newUser").hide();
    //be sure that the add exercise is not shown
    $("#add_exercise").hide();
    //Be sure that user information is shown
    $("#userData").show();
    //Be sure that mainContent is shown
    $("#mainContent").show();
}



/**
 * Helper method to visualize the form to create a new user (#new_user_form)
 * It hides current user information and purge old data still in the form. It 
 * also shows the #createUser button.
**/
function showNewUserForm () {
    //Remove selected users in the sidebar
    deselectUser();

    //Hide the user data, show the newUser div and reset the form
    $("#userData").hide();
    var form =  $("#new_user_form")[0];
    form.reset();
    // Show butons
    $("input[type='button']",form).show();
    
    $("#newUser").show();
    //Be sure that #mainContent is visible.
    $("#mainContent").show();
}

/**
 * Helper method that unselects any user from the #user_list and go back to the
 * initial state by hiding the "#mainContent".
**/
function deselectUser() {
    $("#user_list li.selected").removeClass("selected");
    $("#mainContent").hide();
}

/**
 * Helper method to reload current user's data by making a new API call
 * Internally it makes click on the href of the selected user.
**/
function reloadUserData() {
    var selected = $("#user_list li.selected a");
    selected.click();
}
/*** End of functions that were in the original forum exercise***/
/**** END UI HELPERS ****/

/**** BUTTON HANDLERS ****/

/**
Handles call for handleShowUserForm. 
Runs after it's parent button is clicked.
**/
function handleShowUserForm(event){
    if (DEBUG) {
        console.log ("Triggered handleShowUserForm");
    }
	//make sure modify_user doesn't show
    $("#modify_user").hide();
    showNewUserForm();
	$("#modify_user").hide();
    return false;
}

/**
Handles call for handleShowUserForm. 
Runs after it's parent button is clicked.
**/
function handleCreateUser(event){
    if (DEBUG) {
        console.log ("Triggered handleCreateUser");
    }
    var $form = $(this).closest("form");
    var template = serializeFormTemplate($form);
    var url = $form.attr("action");

    add_user(url, template);

    return false; //Avoid executing the default submit
}
/**
Handles call for Adding a friend. 
Runs after it's parent button is clicked.
calls add_friend funtion that processes the call
**/
function handleAddFriend(event){
    if (DEBUG) {
        console.log ("Triggered handleAddFriend");
    }
	
	event.preventDefault();
	
    add_friend($(this).attr("href"), $("#userHeader").children('input[name="username"]').val(), $("#addFriend").find('input[name="newFriend_text"]').val());
    return false; //Avoid executing the default submit
}
/**
Handles call for removing a friend. 
Runs after it's parent button is clicked.
calls remove_friend function that processes the call
**/
function handleRemoveFriend(event){
    if (DEBUG) {
        console.log ("Triggered handleAddFriend");
    }
    

    event.preventDefault();
    
    remove_friend($(this).attr("href"),$("#userHeader").children('input[name="username"]').val(), $(this).attr("id"))//$("#userHeader").children('input[name="username"]').val(), $("#addFriend").find('input[name="newFriend_text"]').val());
	return false; //Avoid executing the default submit
}
/**
Handles call for to get a user.
Runs after it's parent button is clicked.
calls get_user function that processes the call
**/
function handleGetUser(event) {
    if (DEBUG) {
        console.log ("Triggered handleGetUser");
    }
    event.preventDefault();
    
    $(this).parent().find("selected").removeClass("selected");
    
    $(this).addClass("selected");
    console.log ($(this).attr("href"));
    prepareUserDataVisualization();

	console.log($(this));
    get_user($(this).attr("href"));

   
    return false; //IMPORTANT TO AVOID <A> BUBLING
}
/**
Handles call for to get a exercise.
Runs after it's parent button is clicked.
calls get_exercise function that processes the call
**/
function handleGetExercise(event) {
    if (DEBUG) {
        console.log ("Triggered handleGetExercise");
    }
    event.preventDefault();
    
    $(this).parent().find("selected").removeClass("selected");
    
    $(this).addClass("selected");
    console.log ($(this).attr("href"));
    console.log($(this));
    get_exercise($(this).attr("href"));

   
    return false; //IMPORTANT TO AVOID <A> BUBLING
}
/**
Handles call to find specific user.
Runs after it's parent button is clicked and supplied the data from textbox field.
calls get_user function that processes the call
**/
function handleSearchUser(event) {
    if (DEBUG) {
        console.log ("Triggered handleSearchUser");
    }
    event.preventDefault();

    prepareUserDataVisualization();
	$("#modify_exercise_form").children("div[class=exercise_commands]").hide();
	console.log ("/exercisetracker/api/users/"+$("#search_field").find('input[name="search_field_text"]').val());
    
	get_user("/exercisetracker/api/users/"+$("#search_field").find('input[name="search_field_text"]').val());
 
   
    return false; //IMPORTANT TO AVOID <A> BUBLING
}
/**
Handles call for to add a exercise.
Runs after it's parent button is clicked.
Handles the function and adds necessary data to the form
**/
function handleAddExercise(event) {
    if (DEBUG) {
        console.log ("Triggered handleAddExercise");
    }
    event.preventDefault();

	$.ajax({
                url: "/forum/schema/add-exer/",
                dataType: DEFAULT_DATATYPE
            }).done(function (data, textStatus, jqXHR) {
				console.log(data);
                createFormFromSchema("/exercisetracker/api/exercises/", data, "add_exercise_form");
                //get name from header
                console.log($("#userHeader").children('input[name="username"]').val());
                var name = $("#userHeader").children('input[name="username"]').val();
                //modify string
                name = name.replace("Username: ", "");
                //show form and button
                $("#add_exercise").show();
                $("#exercise_commands").show();
                $("#add_exercise .exercise_commands input[type='button'").show();
                $("#addExercise").show();
                //add username to name field and hide it
                $("#add_exercise").children().children('div[class="form_content"]').children('input[name="username"]').val(name);
                $("#add_exercise").children().children('div[class="form_content"]').children('input[name="username"]').hide();
                $("#add_exercise").children().children('div[class="form_content"]').children('label[for="username"]').hide();
                
            }).fail(function (jqXHR, textStatus, errorThrown) {
                if (DEBUG) {
                    console.log ("RECEIVED ERROR: textStatus:",textStatus, ";error:",errorThrown);
                }
                alert ("Could not fetch form schema.  Please, try again");
            });

    return false; //IMPORTANT TO AVOID <A> BUBLING
}

/**
Handles call for to add a exercise.
Runs after it's parent button is clicked.
calls add_exercise function that processes the call
**/
function handleSubmitAddExercise(event){
    if (DEBUG) {
        console.log ("Triggered handleSubmitAddExercise");
    }
    event.preventDefault();

    var $form = $(this).closest("form");
    var template = serializeFormTemplate($form);
    var url = $form.attr("action");

    
    add_exercise(url, template);
    return false; //Avoid executing the default submit    
}

/**
Handles call for to remove a exercise.
Runs after it's parent button is clicked.
calls remove_exercise function that processes the call
**/
function handleRemoveExercise(event){
    if (DEBUG) {
        console.log ("Triggered handleRemoveExercise");
    }
    event.preventDefault();
	console.log($(this).attr("href"));
	remove_exercise($(this).attr("href"));

    return false; //Avoid executing the default submit    
}

/**
Handles call for to remove a user.
Runs after it's parent button is clicked.
calls remove_user function that processes the call
**/
function handleRemoveUser(event){
    if (DEBUG) {
        console.log ("Triggered handleRemoveUser");
    }
    event.preventDefault();
	console.log($(this).attr("href"));
	remove_user($(this).attr("href"));

    return false; //Avoid executing the default submit    
}

/**
Handles call for to modify User.
Runs after it's parent button is clicked.
Handles the call and shows modify user form
**/
function handleModifyUser(event){
    if (DEBUG) {
        console.log ("Triggered handleModifyUser");
    }
    event.preventDefault();
    //hides user information and shows modify user form
    $("#userData").hide();
    $("#modify_user").show();
    $("#modifyUser").show();
    //hide username field and label becouse they can't be modified but are needed
    $("#modify_user_form").children('div[class=form_content]').children('label[for=username]').hide();
    $("#modify_user_form").children('div[class=form_content]').children('input[name=username]').hide();
    return false; //Avoid executing the default submit    
}

/**
Handles call for to sumbit modified user.
Runs after it's parent button is clicked.
calls modify_user function that processes the call
**/
function handleSubmitModifyUser(event){
    if (DEBUG) {
        console.log ("Triggered handleSubmitModifyUser");
    }
    event.preventDefault();

    var $form = $(this).closest("form");
    var template = serializeFormTemplate($form);
    var url = $form.attr("action");

    modify_user(url , template);
    
    return false; //Avoid executing the default submit    
}

/**
Handles call to show modify exercise form.
Runs after it's parent button is clicked.
Handles the calls and shows modify-exercise form.
**/
function handleModifyExercise(event){
    if (DEBUG) {
        console.log ("Triggered handleModifyExercise");
    }
    event.preventDefault();

    $("#modify_exercise").show();
    $("#modify_exercise_form").children("div[class=exercise_commands]").show();
    $("#modify_exercise_form").children("div[class=exercise_commands]").children().show();    
    return false; //Avoid executing the default submit    
}

/**
Handles call for to sumbit modified exercise.
Runs after it's parent button is clicked.
calls modify_exercise function that processes the call
**/
function handleSubmitModifyExercise(event){
    if (DEBUG) {
        console.log ("Triggered handleSubmitModifyExercise");
    }
    event.preventDefault();

    var $form = $(this).closest("form");
    var template = serializeFormTemplate($form);
    var url = $form.attr("action");

    modify_exercise(url , template);
       
    return false; //Avoid executing the default submit    
}

/**
Handles call for to list all user.
Runs after it's parent button is clicked.
calls getUsers function that processes the call and adds the users to list and shows the list.
**/
function handleShowAllUsers(event){
    if (DEBUG) {
        console.log ("Triggered handleShowAllUsers");
    }
    event.preventDefault();
	getUsers();
	$("#user_list").show();
    $("#showAllUsersButtonContainer").hide();
    $("#hideAllUsersButtonContainer").show();	
    return false; //Avoid executing the default submit    
}

/**
Handles call for to hide user list.
Runs after it's parent button is clicked.
Hides users list.
**/
function handleHideAllUsers(event){
    if (DEBUG) {
        console.log ("Triggered handleHideAllUsers");
    }
    event.preventDefault();
    $("#showAllUsersButtonContainer").show();
    $("#hideAllUsersButtonContainer").hide();		
    $("#user_list").hide();       
    return false; //Avoid executing the default submit    
}

//
/**** END BUTTON HANDLERS ****/

/*** START ON LOAD ***/
//This method is executed when the webpage is loaded.
$(function(){
    $("#addUserButton").on("click", handleShowUserForm);
    $("#createUser").on("click", handleCreateUser);
	$("#add_friend_href").on("click", handleAddFriend);
    
    $("#user_list").on("click","li a" ,handleGetUser);

	$("#search_button").on("click",handleSearchUser);
	$("#add_exercise_button").on("click",handleAddExercise);
    $("#friend_list").on("click","li a" ,handleGetUser);
    $("#remove_friend_list").on("click","li a" ,handleRemoveFriend);

    $("#modify_exercise_button").on("click",handleModifyExercise);
    $("#modifyExercise").on("click",handleSubmitModifyExercise);    
    $("#addExercise").on("click",handleSubmitAddExercise);
    $("#remove_exercise_button").on("click",handleRemoveExercise);
    $("#exercise_list").on("click","li a" ,handleGetExercise);
    
    $("#remove_user_button").on("click",handleRemoveUser);
    $("#modify_user_button").on("click",handleModifyUser);
    $("#modifyUser").on("click",handleSubmitModifyUser);
	$("#showAllUsersButton").on("click", handleShowAllUsers);	
	$("#hideAllUsersButton").on("click", handleHideAllUsers);
	//startup sequence. Creates schemas etc
	startup(ENTRYPOINT);

});
/*** END ON LOAD**/
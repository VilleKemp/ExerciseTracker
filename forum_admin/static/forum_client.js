/**
 * @fileOverview Forum administration dashboard. It utilizes the Forum API to 
                 handle user information (retrieve user list, edit user profile, 
                 as well as add and remove new users form the system). It also 
                 permits to list and remove user's messages.
 * @author <a href="mailto:ivan.sanchez@oulu.fi">Ivan Sanchez Milara</a>
 * @author <a href="mailto:mika.oja@oulu.fi">Mika Oja</a>
 * @version 1.0
 * 
 * NOTE: The documentation utilizes jQuery syntax to refer to classes and ids in
         the HTML code: # is utilized to refer to HTML elements ids while . is
         utilized to refer to HTML elements classes.
**/


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
 * Link to Messages_profile
 * @constant {string}
 * @default 
 */
const FORUM_MESSAGE_PROFILE = "/profiles/messages";

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

/**** Description of the functions that call Forum API by means of jQuery.ajax()
      calls. We have implemented one function per link relation in both profiles.
      Since we are not interesting in the whole API functionality, some of the
      functions does not do anything. Hence, those link relations are ignored
****/ 


/**
 * This function is the entrypoint to the Forum API.
 *
 * Associated rel attribute: Users Mason+JSON and users-all
 * 
 * Sends an AJAX GET request to retrive the list of all the users of the application
 * 
 * ONSUCCESS=> Show users in the #user_list. 
 *             After processing the response it utilizes the method {@link #appendUserToList}
 *             to append the user to the list.  
 *             Each user is an anchor pointing to the respective user url.
 * ONERROR => Show an alert to the user.
 *
 * @param {string} [apiurl = ENTRYPOINT] - The url of the Users instance.
**/
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
            appendUserToList(user["@controls"].self.href, user.username)
        }

        //Prepare the new_user_form to create a new user
        var create_ctrl = data["@controls"]["add user"]
        
        if (create_ctrl.schema) {
            
            createFormFromSchema(create_ctrl.href, create_ctrl.schema, "new_user_form");
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
    }).fail(function (jqXHR, textStatus, errorThrown){
        if (DEBUG) {
            console.log ("RECEIVED ERROR: textStatus:",textStatus, ";error:",errorThrown);
        }
        //Inform user about the error using an alert message.
        alert ("Could not fetch the list of users.  Please, try again");
    });
}

function getUsersFriends(apiurl) {
    apiurl = apiurl || ENTRYPOINT;
    //$("#mainContent").hide();
    return $.ajax({
        url: apiurl,
        dataType:DEFAULT_DATATYPE,
        contentType: 'application/json'
    }).always(function(){
        //Remove old list of users
        //clear the form data hide the content information(no selected)
        $("#friend_list").empty();
        //$("#mainContent").hide();

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
            friend_links = friend["@controls"];
            friend_links["remove-friend"].href;
            console.log("HREF: " + friend["@controls"].self.href + "   Friendname:" + friend.friend);
            appendFriendToList(friend["@controls"].self.href,friend.friend);
            //friend_links["remove-friend"].href,
        }
        
    }).fail(function (jqXHR, textStatus, errorThrown){
        if (DEBUG) {
            console.log ("RECEIVED ERROR: textStatus:",textStatus, ";error:",errorThrown, "URL: apiurl:", apiurl);
                    }
        //Inform user about the error using an alert message.
        //alert ("Could not fetch the list of friends.  Please, try again");
    });
}

//own stuff

function remove_user(apiurl){
	return $.ajax({
		url: apiurl, //The URL of the resource
		type: "DELETE", //The resource method
        dataType:DEFAULT_DATATYPE,
		contentType: 'application/json'
    }).done(function (data, textStatus, jqXHR){

		//hides exercise information. migth be smarter to empty?
		$("#userData").hide();
		
	});		
}

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

function startup(apiurl) {
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
                console.log("####AREWERE##");
                console.log(create_ctrl.href);
                console.log(data);
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

function getUsersExercises(apiurl, username) {
    apiurl = apiurl || ENTRYPOINT;
    //$("#mainContent").hide();
    return $.ajax({
        url: apiurl,
        dataType:DEFAULT_DATATYPE,
		contentType: 'application/json'
    }).always(function(){
        //Remove old list of users
        //clear the form data hide the content information(no selected)
        $("#exercise_list").empty();
        //$("#mainContent").hide();

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
    
    

/*** RELATIONS USED IN MESSAGES AND USERS PROFILES ***/

/**
 * Associated rel attribute: users-all
 * @see {@link #getUsers}
**/
function users_all(apiurl){
    return getUsers(apiurl);
}

/**
 * This client does not support this functionality.
 *
 * Associated rel attribute: messages-all
 *
 * @param {string} apiurl - The url of the Messages list.
**/
function messages_all(apiurl){
    return; //THE CLIENT DOES NOT KNOW HOW TO HANDLE LIST OF MESSAGES
}

/*** FUNCTIONS FOR MESSAGE PROFILE ***/

/*** Note, the client is mainly utilized to manage users, not to manage
messages ***/


/**
 * This client does not support this functionality.
 *
 * Associated rel attribute: reply
 *
 * @param {string} apiurl - The url of the parent message.
 * @param {object} body - An associative array with the new message
 * 
**/
function reply(apiurl,body){
    return; //THE CLIENT DOES NOT KNOW HOW TO ADD A NEW MESSAGE
}

/**
 * Sends an AJAX request to remove a message from the system. Utilizes the DELETE method.
 *
 * Associated rel attribute: delete (in Message profile)
 * ONSUCCESS=>
 *          a) Inform the user with an alert.
 *          b) Go to the initial state by calling the function {@link #reloadUserData} *
 *
 * ONERROR => Show an alert to the user
 *
 * @param {string} apiurl - The url of the Message
 * 
**/
    
function delete_message(apiurl){
    //TODO 3: Send an AJAX request to remove the current message
        // Do not implement the handlers yet, just show some DEBUG text in the console.
        // You just need to send a $.ajax request of type "DELETE". No extra parameters
        //are required.
    //TODO 4
       //Implemente the handlers following the instructions from the function documentation.
    $.ajax({
       url: apiurl, //The URL of the resource
       type: "DELETE", //The resource method
      // dataType:RESPONSE_FORMAT, //The format expected in the
 //response : xml or json
       headers: {"Authorization":"admin"}// An object containing
 //headers
    }).done(function (data, textStatus, jqXHR){
       alert("message deleted");
       reloadUserData();

    }).fail(function (jqXHR, textStatus, errorThrown){
        alert("couldn't delete message");
    });
}

/**
 * This client does not support this functionality.
 *
 * Associated rel attribute: add-message
 *
 * @param {string} apiurl - The url of the parent Messages collection
 * 
**/

function delete_exercise(apiurl){
    //TODO 3: Send an AJAX request to remove the current message
        // Do not implement the handlers yet, just show some DEBUG text in the console.
        // You just need to send a $.ajax request of type "DELETE". No extra parameters
        //are required.
    //TODO 4
       //Implemente the handlers following the instructions from the function documentation.
    $.ajax({
       url: apiurl, //The URL of the resource
       type: "DELETE", //The resource method
      // dataType:RESPONSE_FORMAT, //The format expected in the
 //response : xml or json
       headers: {"Authorization":"admin"}// An object containing
 //headers
    }).done(function (data, textStatus, jqXHR){
       alert("exercise deleted");
       reloadUserData();

    }).fail(function (jqXHR, textStatus, errorThrown){
        alert("couldn't delete exercise");
    });
}

/**
 * This client does not support this functionality.
 *
 * Associated rel attribute: add-message
 *
 * @param {string} apiurl - The url of the parent Messages collection
 * 
**/

function add_message(apiurl,template){
    return; //THE CLIENT DOES NOT KNOW HOW TO HANDLE COLLECTION OF MESSAGES
}

/**
 * This client does not support this functionality.
 *
 * Associated rel attribute: author
 *
 * @param {string} apiurl - The url of the User instance.
**/
function author(apiurl){
    return; //THE CLIEND DOES NOT KNOW TO HANDLE THIS RELATION.
}

/**
 * This client does not support this functionality.
 *
 * Associated rel attribute: collection (message_profile)
 *
 * @param {string} apiurl - The url of the Messages list.
**/
function collection_messages(apiurl){
    return; //THE CLIENT DOES NOT KNOW HOW TO HANDLE A LIST OF MESSAGES
}

/**
 * This client does not support this functionality.
 *
 * Associated rel attribute: edit (in message profile)
 *
 * @param {string} apiurl - The url of the Message
 * @param {object} message - An associative array containing the new information 
 *   of the message
 * 
**/
function edit_message(apiurl, template){
    return; //THE CLIENT DOES NOT KNOW HOW TO HANDLE COLLECTION OF MESSAGES
}

/**
 * This client does not support this functionality.
 *
 * Associated rel attribute: in-reply-to
 *
 * @param {string} apiurl - The url of the Message
**/
function in_reply_to(apiurl){
    return; //THE CLIENT DOES NOT KNOW HOW TO REPRESENT A HIERARHCY OF MESSAGEs

}

/**
 * Sends an AJAX request to retrieve message information Utilizes the GET method.
 *
 * Associated rel attribute: self (in message profile)
 *
 * ONSUCCESS=>
 *          a) Extract message information from the response body. The response
 *             utilizes a HAL format.
 *          b) Show the message headline and articleBody in the UI. Call the helper
 *             method {@link appendMessageToList}
 *
 * ONERROR => Show an alert to the user
 *
 * @param {string} apiurl - The url of the Message
 * 
**/

function get_message(apiurl){
    $.ajax({
        url: apiurl,
        dataType:DEFAULT_DATATYPE
    }).done(function (data, textStatus, jqXHR){
        if (DEBUG) {
            console.log ("RECEIVED RESPONSE: data:",data,"; textStatus:",textStatus);
        }
        var message_url = data["@controls"].self.href;
        var headline = data.headline;
        var articleBody =  data.articleBody;
        appendMessageToList(message_url, headline, articleBody);

    }).fail(function (jqXHR, textStatus, errorThrown){
        if (DEBUG) {
            console.log ("RECEIVED ERROR: textStatus:",textStatus, ";error:",errorThrown);
        }
        alert("Cannot get information from message: "+ apiurl);
    });
}


/*** FUNCTIONS FOR USER PROFILE ***/

/**
 * Sends an AJAX GET request to retrieve information related to user history.
 *
 * Associated rel attribute: messages-history 
 *
 * ONSUCCESS =>
 *   a.1) Check the number of messages received (data.items) 
 *   a.2) Add the previous value to the #messageNumber input element (located in 
 *        #userHeader section).
 *   b.1) Iterate through all messages. 
 *   b.2) For each message in the history, access the message information by
 *        calling the corresponding Message instance (call {@link get_message})
 *        The url of the message is obtained from the href attribute of the
 *        message item. 
 * ONERROR =>
 *    a)Show an *alert* informing the user that the target user history could not be retrieved
 *    b)Deselect current user calling {@link #deselectUser}.
 * @param {string} apiurl - The url of the History instance.
**/
    //TODO 3: Send the AJAX to retrieve the history information. 
    //        Do not implement the handlers yet, just show some DEBUG text in the console.
    //TODO 4: Implement the handlers for done() and fail() responses 
    
function messages_history(apiurl){
    return $.ajax({
   url: apiurl, //The URL of the resource
   type: "GET", //The resource method
 //response : xml or json
   headers: {"Authorization":"admin"}// An object containing
 //headers    
    
    }).done(function (data, textStatus, jqXHR){
   
    var mnumber=data.items.length;
      
    $("#messagesNumber").val(mnumber);

            
        messages = data.items;
        for (var i=0; i < messages.length; i++){
            var message = messages[i];
            
            //Extract the username by getting the data values. Once obtained
            // the username use the method appendUserToList to show the user
            // information in the UI.
            
            get_message(message["@controls"].self.href);
           // appendUserToList(user["@controls"].self.href, user.username)
        }
    
    
    //{@link get_message(data.items[i].attr("href"))};
        
    
    }).fail(function (jqXHR, textStatus, errorThrown){
       alert("message_history fail");
       deselectUser();
    });
}

/**
 * Sends an AJAX request to delete an user from the system. Utilizes the DELETE method.
 *
 * Associated rel attribute: delete (User profile)
 *
 *ONSUCCESS =>
 *    a)Show an alert informing the user that the user has been deleted
 *    b)Reload the list of users: {@link #getUsers}
 *
 * ONERROR =>
 *     a)Show an alert informing the user that the new information was not stored in the databse
 *
 * @param {string} apiurl - The url of the intance to delete. 
**/
function delete_user(apiurl){
    $.ajax({
        url: apiurl,
        type: "DELETE",
    }).done(function (data, textStatus, jqXHR){
        if (DEBUG) {
            console.log ("RECEIVED RESPONSE: data:",data,"; textStatus:",textStatus);
        }
        alert ("The user information has been deleted from the database");
        //Update the list of users from the server.
        getUsers();

    }).fail(function (jqXHR, textStatus, errorThrown){
        if (DEBUG) {
            console.log ("RECEIVED ERROR: textStatus:",textStatus, ";error:",errorThrown);
        }
        alert ("The user information could not be deleted from the database");
    });
}

/**
 * This client does not support handling public user information
 *
 * Associated rel attribute: public-data
 * 
 * @param {string} apiurl - The url of the Public profile instance.
**/
function public_data(apiurl){
    return; // THE CLIENT DOES NOT SHOW USER PUBLIC DATA SUCH AVATAR OR IMAGE

}

/**
 * Sends an AJAX request to retrieve the restricted profile information:
 * {@link http://docs.pwpforum2017appcompleteversion.apiary.io/#reference/users/users-private-profile/get-user's-restricted-profile | User Restricted Profile}
 * 
 * Associated rel attribute: private-data
 * 
 * ONSUCCESS =>
 *  a) Extract all the links relations and its corresponding URLs (href)
 *  b) Create a form and fill it with attribute data (semantic descriptors) coming
 *     from the request body. The generated form should be embedded into #user_restricted_form.
 *     All those tasks are performed by the method {@link #fillFormWithMasonData}
 *     b.1) If "user:edit" relation exists add its href to the form action attribute. 
 *          In addition make the fields editables and use template to add missing
 *          fields. 
 *  c) Add buttons to the previous generated form.
 *      c.1) If "user:delete" relation exists show the #deleteUserRestricted button
 *      c.2) If "user:edit" relation exists show the #editUserRestricted button
 *
 * ONERROR =>
 *   a)Show an alert informing the restricted profile could not be retrieved and
 *     that the data shown in the screen is not complete.
 *   b)Unselect current user and go to initial state by calling {@link #deselectUser}
 * 
 * @param {string} apiurl - The url of the Restricted Profile instance.
**/
function private_data(apiurl){
    return $.ajax({
            url: apiurl,
            dataType:DEFAULT_DATATYPE,
        }).done(function (data, textStatus, jqXHR){
            if (DEBUG) {
            console.log ("RECEIVED RESPONSE: data:",data,"; textStatus:",textStatus);
            }
            //Extract links
            var user_links = data["@controls"];
            var schema, resource_url = null;
            if ("forum:delete" in user_links){
                resource_url = user_links["forum:delete"].href; // User delete link
                $("#deleteUserRestricted").show();
            }
            if ("edit" in user_links){
                resource_url = user_links["edit"].href;
                //Extract the template value
                schema = user_links["edit"].schema;
                if (user_links["edit"].schema) {
                    $form = createFormFromSchema(resource_url, schema, "user_restricted_form");
                    $("#editUserRestricted").show();
                    fillFormWithMasonData($form, data);
                }
                else if (user_links["edit"].schemaUrl) {
                    $.ajax({
                        url: user_links["edit"].schemaUrl,
                        dataType: DEFAULT_DATATYPE
                    }).done(function (schema, textStatus, jqXHR) {
                        $form = createFormFromSchema(resource_url, schema, "user_restricted_form");
                        $("#editUserRestricted").show();
                        fillFormWithMasonData($form, data);                        
                    }).fail(function (jqXHR, textStatus, errorThrown) {
                        if (DEBUG) {
                            console.log ("RECEIVED ERROR: textStatus:",textStatus, ";error:",errorThrown);
                        }
                        alert ("Could not fetch form schema.  Please, try again");
                    });
                }
                else {
                    alert("Form schema not found");
                }
            }            
            
        }).fail(function (jqXHR, textStatus, errorThrown){
            if (DEBUG) {
                console.log ("RECEIVED ERROR: textStatus:",textStatus, ";error:",errorThrown);
            }
            //Show an alert informing that I cannot get info from the user.
            alert ("Cannot extract all the information about this user from the server");
            deselectUser();
        });
}

/**
 * Sends an AJAX request to create a new user {@link http://docs.pwpforum2017appcompleteversion.apiary.io/#reference/users/user}
 *
 * Associated link relation: add_user
 *
 *  ONSUCCESS =>
 *       a) Show an alert informing the user that the user information has been modified
 *       b) Append the user to the list of users by calling {@link #appendUserToList}
 *          * The url of the resource is in the Location header
 *          * {@link #appendUserToList} returns the li element that has been added.
 *       c) Make a click() on the added li element. To show the created user's information.
 *     
 * ONERROR =>
 *      a) Show an alert informing that the new information was not stored in the databse
 * 
 * @param {string} apiurl - The url of the User instance. 
 * @param {object} user - An associative array containing the new user's information
 * 
**/   

function add_exercise(apiurl,exercise){
    var exerciseData = JSON.stringify(exercise);
    return $.ajax({
        url: apiurl,
        type: "POST",
        dataType:DEFAULT_DATATYPE,
        data:exerciseData,
        //processData:false,
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


function add_user(apiurl,user){
    var userData = JSON.stringify(user);
    var username = user.username;
    return $.ajax({
        url: apiurl,
        type: "POST",
        dataType:DEFAULT_DATATYPE,
        data:userData,
        //processData:false,
        contentType: PLAINJSON
    }).done(function (data, textStatus, jqXHR){
        if (DEBUG) {
            console.log ("RECEIVED RESPONSE: data:",data,"; textStatus:",textStatus);
        }
        alert ("User successfully added");
        //Add the user to the list and load it.
		

		

    }).fail(function (jqXHR, textStatus, errorThrown){
        if (DEBUG) {
            console.log ("RECEIVED ERROR: textStatus:",textStatus, ";error:",errorThrown);
        }
        alert ("Could not create new user:"+jqXHR.responseJSON.message);
    });
}

/**Get all users.
 *
 * Associated rel attribute: collection (user profile)
 *
 * @param {string} apiurl - The url of the Users list.
 * @see {@link #getUsers}
**/
function collection_users(apiurl){
    return users_all(apirul);
}

/**
 * Get user information. 
 *
 * Associated rel attribute: up
 *
 * @param {string} apiurl - The url of the User instamce
**/
function up(apiurl){
    return; //We do not process this information. 
}

/**
 * Sends an AJAX request to modify the restricted profile of a user, using PUT
 *
 * NOTE: This is NOT utilizied in this application.
 *
 * Associated rel attribute: edit (user profile)
 *
 * ONSUCCESS =>
 *     a)Show an alert informing the user that the user information has been modified
 * ONERROR =>
 *     a)Show an alert informing the user that the new information was not stored in the databse
 * 
 * @param {string} apiurl - The url of the intance to edit. 
 * @param {object} body - An associative array containing the new data of the
 *  target user
 * 
**/
function edit_user(apiurl, body){
    $.ajax({
        url: apiurl,
        type: "PUT",
        data:JSON.stringify(body),
        processData:false,
        contentType: PLAINJSON
    }).done(function (data, textStatus, jqXHR){
        if (DEBUG) {
            console.log ("RECEIVED RESPONSE: data:",data,"; textStatus:",textStatus);
        }
        alert ("User information have been modified successfully");

    }).fail(function (jqXHR, textStatus, errorThrown){
        if (DEBUG) {
            console.log ("RECEIVED ERROR: textStatus:",textStatus, ";error:",errorThrown);
        }
        var error_message = $.parseJSON(jqXHR.responseText).message;
        alert ("Could not modify user information;\r\n"+error_message);
    });
}

/**
 * Sends an AJAX request to retrieve information related to a User {@link http://docs.pwpforum2017appcompleteversion.apiary.io/#reference/users/user}
 *
 * Associated link relation:self (inside the user profile)
 *
 *  ONSUCCESS =>
 *              a) Fill basic user information: username and registrationdate.
 *                  Extract the information from the attribute input
 *              b) Extract associated link relations from the response
 *                    b.1) If user:delete: Show the #deleteUser button. Add the href
 *                        to the #user_form action attribute.
 *                    b.2) If user:edit: Show the #editUser button. Add the href
 *                        to the #user_form action attribute.
 *                    b.3) If user:restricted data: Call the function {@link #private_data} to 
 *                        extract the information of the restricted profile
 *                    b.4) If user:messages: Call the function {@link #messages_history} to extract
 *                        the messages history of the current user.  *
 *
 * ONERROR =>   a) Alert the user
 *              b) Unselect the user from the list and go back to initial state 
 *                (Call {@link deleselectUser})
 * 
 * @param {string} apiurl - The url of the User instance. 
**/
function get_user(apiurl) {
    return $.ajax({
        //url: apiurl,
        //dataType:DEFAULT_DATATYPE,
		//contentType: 'application/json',
        //processData:false,
		url: apiurl,
        dataType:DEFAULT_DATATYPE,
		contentType: 'application/json'
    }).done(function (data, textStatus, jqXHR){
        if (DEBUG) {
            console.log ("RECEIVED RESPONSE: data:",data,"; textStatus:",textStatus);
			//console.log ( "" + data[1]);
        }


        //Fill basic information from the user_basic_form
        console.log("###HEERE###");
        console.log(data);
        $("#username").val("Username: " + data.username);
		$("#visibility").val("Visibility: " + data.visibility || "??");
		$("#description").val("Description: " + data.description || "??");
		$("#password").val(data.password || "??");
		$("#avatar").val("Avatar: " +data.avatar || "??");
        //delete(data.username);
        //$("#registrationdate").val(getDate(data.registrationdate || 0));
        //delete(data.registrationdate);
        //$("#messagesNumber").val("??");
		

		
        //Extract user information
        var user_links = data["@controls"];
		console.log("#userlinks");
		console.log(user_links);
		
		if("delete user information" in user_links)
		{
		$("#remove_user_button").attr("href",user_links["delete user information"].href);	
			
		}
		//remove stuff from below?
        //Extracts urls from links. I need to get if the different links in the
        //response.
        if("list-friends" in user_links)
        {
            var friends_url = user_links["list-friends"].href;
        }
        if("add-friend" in user_links)
        {
            var my_friend_url = user_links["add-friend"].href;
            console.log(user_links["add-friend"].href);
        }


        if ("forum:private-data" in user_links) {
           var private_profile_url = user_links["forum:private-data"].href; //Restricted profile
        }
        if ("forum:messages-history" in user_links){            
            var messages_url = user_links["forum:messages-history"].href;
            // cut out the optional query parameters. this solution is not pretty. 
            messages_url = messages_url.slice(0, messages_url.indexOf("{?")); 
        }
        if ("forum:delete" in user_links)
            var delete_link = user_links["forum:delete"].href; // User delete linke
        if ("edit" in user_links)
            var edit_link = user_links["edit"].href;
		
		if (delete_link){
            $("#user_form").attr("action", delete_link);
            $("#deleteUser").show();
        }
        if (delete_link){
            $("#user_form").attr("action", delete_link);
            $("#deleteUser").show();
        }
        if (edit_link){
            $("#user_form").attr("action", edit_link);
            $("#editUser").show();
        }
		if (my_friend_url ){
            $("#add_friend_href").attr("href", user_links["add-friend"].href);

            //$("#addFriend").show();
        }
        //Fill the user profile with restricted user profile. This method
        // Will call also to the list of messages.
        if (private_profile_url){
            private_data(private_profile_url);
        }
        //Get the history link and ask for history.
        if (messages_url){
            messages_history(messages_url);
        }
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
	
	/*
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
            appendUserToList(user["@controls"].self.href, user.username)
        }

        //Prepare the new_user_form to create a new user
        var create_ctrl = data["@controls"]["add user"]
        
        if (create_ctrl.schema) {
            createFormFromSchema(create_ctrl.href, create_ctrl.schema, "new_user_form");
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
    }).fail(function (jqXHR, textStatus, errorThrown){
        if (DEBUG) {
            console.log ("RECEIVED ERROR: textStatus:",textStatus, ";error:",errorThrown);
        }
        //Inform user about the error using an alert message.
        alert ("Could not fetch the list of users.  Please, try again");
    });*/
}

function get_exercise(apiurl) {
    return $.ajax({
        //url: apiurl,
        //dataType:DEFAULT_DATATYPE,
        //contentType: 'application/json',
        //processData:false,
        url: apiurl,
        dataType:DEFAULT_DATATYPE,
        contentType: 'application/json'
    }).done(function (data, textStatus, jqXHR){
        if (DEBUG) {
            console.log ("RECEIVED RESPONSE: data:",data,"; textStatus:",textStatus);
            //console.log ( "" + data[1]);
        }

		//make sure exercise data is shown
		$("#exerciseData").show();
		
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
            
        //Extracts urls from links. I need to get if the different links in the
        //response.
        /*if ("forum:private-data" in user_links) {
           var private_profile_url = user_links["forum:private-data"].href; //Restricted profile
        }
        if ("forum:messages-history" in user_links){            
            var messages_url = user_links["forum:messages-history"].href;
            // cut out the optional query parameters. this solution is not pretty. 
            messages_url = messages_url.slice(0, messages_url.indexOf("{?")); 
        }
        if ("forum:delete" in user_links)
            var delete_link = user_links["forum:delete"].href; // User delete linke
        if ("edit" in user_links)
            var edit_link = user_links["edit"].href;*/
        /*
        if (delete_link){
            //$("#user_form").attr("action", delete_link);
            $("#deleteExercise").show();
        }
        */
        /*if (edit_link){
            $("#user_form").attr("action", edit_link);
            $("#editUser").show();
        }*/


    }).fail(function (jqXHR, textStatus, errorThrown){
        if (DEBUG) {
            console.log ("RECEIVED ERROR: textStatus:",textStatus, ";error:",errorThrown);
        }
        //Show an alert informing that I cannot get info from the user.
        alert ("Cannot extract information about this exercise");
        //Deselect the user from the list.
        //deselectUser();
    });

}

function add_friend(apiurl,username, friendname){
    
    //var username = user.username;
    var name = username;// $("#userHeader").children('input[name="username"]').val();
    //var name = $("#userHeader").find('input[name="username"]').val()

    name = name.replace("Username: ", "");
    var Data = {"username":name, "friendname":friendname};
    var userData = JSON.stringify(Data);
    //headers: {"Authorization":"admin", }
	console.log ("RECEIVED URL: url:",apiurl, "; Received DATA:", userData);
    return $.ajax({
        url: apiurl,
        type: "POST",
        dataType:DEFAULT_DATATYPE,
        data:userData,
        //processData:false,
        contentType: PLAINJSON
    }).done(function (data, textStatus, jqXHR){
        if (DEBUG) {
            console.log ("RECEIVEEED RESPONSE: data:",data,"; textStatus:",textStatus);
        }
        getUsersFriends(apiurl)
        alert ("Friend successfully added");
        //Add the user to the list and load it.
		

		

    }).fail(function (jqXHR, textStatus, errorThrown){
        if (DEBUG) {
            console.log ("RECEIVED ERROR: textStatus:",textStatus, ";error:",errorThrown);
        }
        alert ("Could not create new user:"+jqXHR.responseJSON.message);
    });
}

function remove_friend(apiurl,username, friendname){
    
    //var username = user.username;
    var name = username;// $("#userHeader").children('input[name="username"]').val();
    //var name = $("#userHeader").find('input[name="username"]').val()

    name = name.replace("Username: ", "");
    var Data = {"username":name, "friendname":friendname};
    var userData = JSON.stringify(Data);
    //headers: {"Authorization":"admin", }
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
        //Add the user to the list and load it.
        

        

    }).fail(function (jqXHR, textStatus, errorThrown){
        if (DEBUG) {
            console.log ("RECEIVED ERROR: textStatus:",textStatus, ";error:",errorThrown);
        }
        alert ("Could not delete friend:"+jqXHR.responseJSON.message);
    });
}
   
/**** END RESTFUL CLIENT****/

/**** UI HELPERS ****/

/**** This functions are utilized by rest of the functions to interact with the
      UI ****/

/**
 * Append a new user to the #user_list. It appends a new <li> element in the #user_list 
 * using the information received in the arguments.  
 *
 * @param {string} url - The url of the User to be added to the list
 * @param {string} username - The username of the User to be added to the list
 * @returns {Object} The jQuery representation of the generated <li> elements.
**/
function appendUserToList(url, username) {
    var $user = $('<li>').html('<a class= "user_link" href="'+url+'">'+username+'</a>');
    //Add to the user list
    $("#user_list").append($user);
    return $user;
}
function appendFriendToList(url, removeurl, friendname) {
    var $friend = $('<li>').html('<a class= "user_link" href="'+url+'">'+friendname+'</a>');
    //var $removefriend = $('<li>').html('<a class= "user_link" href="'+removeurl+'">'+"Remove"+'</a>');
    //$("#add_friend_href").attr("href", user_links["add-friend"].href);
    //Add to the user list
    $("#friend_list").append($friend);
    //$("#remove_friend_list").append($removefriend);
    return $friend;
}

function appendExerciseToList(url, type, date) {
    var $exercise = $('<li>').html('<a class= "exercise_link" href="'+url+'">'+type+ " " + date +'</a>');
    //Add to the user list
    $("#exercise_list").append($exercise);
    return $exercise;

    /*var $exercise = $("<div>").addClass('exercise').html(""+
                        "<form action='"+url+"'>"+
                        "   <div class='form_content'>"+
                        "       <input type=text class='type' value='"+type+"' readonly='readonly'/>"+
                        "       <div class='articlebody'>"+articlebody+"</div>"+
                        "   </div>"+
                        "   <div class='commands'>"+
                        "        <input type='button' class='deleteButton deleteExercise' value='Delete'/>"+
                        "   </div>" +
                        "</form>"
                    );
    //Append to list
    $("#exercise_list").append($exercise);*/
}

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
 * Add a new .message HTML element in the to the #messages_list <div> element.
 * The format of the generated HTML is the following:
 * @example
 *  //<div class='message'>
 *  //        <form action='#'>
 *  //            <div class="commands">
 *  //                <input type="button" class="editButton editMessage" value="Edit"/>
 *  //                <input type="button" class="deleteButton deleteMessage" value="Delete"/>
 *  //             </div>
 *  //             <div class="form_content">
 *  //                <input type=text class="headline">
 *  //                <input type="textarea" class="articlebody">
 *  //             </div>  
 *  //        </form>
 *  //</div>
 *
 * @param {string} url - The url of the created message
 * @param {string} headline - The title of the new message
 * @param {string} articlebody - The body of the crated message. 
**/
function appendMessageToList(url, headline, articlebody) {
        
    var $message = $("<div>").addClass('message').html(""+
                        "<form action='"+url+"'>"+
                        "   <div class='form_content'>"+
                        "       <input type=text class='headline' value='"+headline+"' readonly='readonly'/>"+
                        "       <div class='articlebody'>"+articlebody+"</div>"+
                        "   </div>"+
                        "   <div class='commands'>"+
                        "        <input type='button' class='deleteButton deleteMessage' value='Delete'/>"+
                        "   </div>" +
                        "</form>"
                    );
    //Append to list
    $("#messages_list").append($message);
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

/**
 * Transform a date given in a UNIX timestamp into a more user friendly string
 * 
 * @param {number} timestamp - UNIX timestamp
 * @returns {string} A string representation of the UNIX timestamp with the 
 * format: 'dd.mm.yyyy at hh:mm:ss'
**/
function getDate(timestamp){
    // create a new javascript Date object based on the timestamp
    // multiplied by 1000 so that the argument is in milliseconds, not seconds
    var date = new Date(timestamp*1000);
    // hours part from the timestamp
    var hours = date.getHours();
    // minutes part from the timestamp
    var minutes = date.getMinutes();
    // seconds part from the timestamp
    var seconds = date.getSeconds();

    var day = date.getDate();

    var month = date.getMonth()+1;

    var year = date.getFullYear();

    // will display time in 10:30:23 format
    return day+"."+month+"."+year+ " at "+ hours + ':' + minutes + ':' + seconds;
}

/** 
 * Transforms an address with the format 'city, country' into a dictionary.
 * @param {string} input - The address to be converted into a dictionary with the
 * format 'city, country'
 * @returns {Object} a dictionary with the following format: 
 * {'object':{'addressLocality':locality, 'addressCountry':country}}
**/
function getAddress(address){
    var _address = address.split(",",2);
    return {'addressLocality':_address[0], 'addressCountry':_address[1]||"??"};

}
/**** END UI HELPERS ****/

/**** BUTTON HANDLERS ****/

/**
 * Shows in #mainContent the #new_user_form. Internally it calls to {@link #showNewUserForm}
 *
 * TRIGGER: #addUserButton
**/
function handleShowUserForm(event){
    if (DEBUG) {
        console.log ("Triggered handleShowUserForm");
    }
    //Show the form. Note that the form was updated when I apply the user collection
    showNewUserForm();
    return false;
}

/**
 * Uses the API to delete the currently selected user.
 *
 * TRIGGER: #deleteUser 
**/
function handleDeleteUser(event){
    //Extract the url of the resource from the form action attribute.
    if (DEBUG) {
        console.log ("Triggered handleDeleteUser");
    }

    var userurl = $(this).closest("form").attr("action");
    users_collection_delete_item(userurl);
}

/**
 * Uses the API to update the user's with the form attributes in the present form.
 *
 * TRIGGER: #editUser 
**/
function handleEditUser(event){
    if (DEBUG) {
        console.log ("Triggered handleEditUser");
    }
    var $form = $(this).closest("form");
    var body = serializeFormTemplate($form);
    var url = $form.attr("action");
    users_collection_edit_item(url, body);
    return false; //Avoid executing the default submit
}

/**
 * Uses the API to delete the restricted profile of the selected user.
 *
 * TRIGGER: #deleteRestrictedUser
**/
function handleDeleteUserRestricted(event){
    //Extract the url of the resource from the form action attribute.
    if (DEBUG) {
        console.log ("Triggered handleDeleteUserRestricted");
    }

    var user_restricted_url = $(this).closest("form").attr("action");
    delete_user(user_restricted_url);
}

/**
 * Uses the API to update the user's restricted profile with the form attributes in the present form.
 *
 * TRIGGER: #editRestrictedUser 
**/
function handleEditUserRestricted(event){
    //Extract the url of the resource from the form action attribute.
    if (DEBUG) {
        console.log ("Triggered handleDeleteUserRestricted");
    }
    var $form = $(this).closest("form");
    var body = serializeFormTemplate($form);
    var user_restricted_url = $(this).closest("form").attr("action");
    edit_user(user_restricted_url, body);
}

/**
 * Uses the API to create a new user with the form attributes in the present form.
 *
 * TRIGGER: #createUser 
**/
function handleCreateUser(event){
    if (DEBUG) {
        console.log ("Triggered handleCreateUser");
    }
    var $form = $(this).closest("form");
    var template = serializeFormTemplate($form);
    var url = $form.attr("action");
	console.log("#####################");
	console.log(template);
	console.log(url);
	console.log("#####################");
    add_user(url, template);
    return false; //Avoid executing the default submit
}

function handleAddFriend(event){
    if (DEBUG) {
        console.log ("Triggered handleAddFriend");
    }
	
	event.preventDefault();
	//prepareUserDataVisualization();
	

	//console.log ("RECEIVED URL: url:",$(this).attr("href"));
	//get_user("/exercisetracker/api/users/"+$("#search_field").find('input[name="search_field_text"]').val());
    
    add_friend($(this).attr("href"), $("#userHeader").children('input[name="username"]').val(), $("#addFriend").find('input[name="newFriend_text"]').val());
    return false; //Avoid executing the default submit
}

function handleRemoveFriend(event){
    if (DEBUG) {
        console.log ("Triggered handleAddFriend");
    }
    

    event.preventDefault();
    //prepareUserDataVisualization();
    

    //console.log ("RECEIVED URL: url:",$(this).attr("href"));
    //get_user("/exercisetracker/api/users/"+$("#search_field").find('input[name="search_field_text"]').val());
    
    remove_friend($(this).attr("href"), $("#userHeader").children('input[name="username"]').val(), $("#addFriend").find('input[name="newFriend_text"]').val());
    return false; //Avoid executing the default submit
}
/**
 * Uses the API to retrieve user's information from the clicked user. In addition, 
 * this function modifies the selected user in the #user_list (removes the .selected
 * class from the old user and add it to the current user)
 *
 * TRIGGER: click on #user_list li a 
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

function handleGetExercise(event) {
    if (DEBUG) {
        console.log ("Triggered handleGetExercise");
    }
    event.preventDefault();
    
    $(this).parent().find("selected").removeClass("selected");
    
    $(this).addClass("selected");
    console.log ($(this).attr("href"));
    //prepareUserDataVisualization();
    console.log($(this));
    get_exercise($(this).attr("href"));

   
    return false; //IMPORTANT TO AVOID <A> BUBLING
}


/**
 * Uses the API to delete the associated message
 *
 * TRIGGER: .deleteMessage
**/
function handleDeleteMessage(event){
    if (DEBUG) {
        console.log ("Triggered handleDeleteMessage");
    }
    var messageurl = $(this).closest("form").attr("action");
    delete_message(messageurl);    
    //TODO 2:
    //  Extract the url of the resource to be deleted from the form action attribute.
    //  Call the method delete_message(messageurl).
    //  Check handleDeleteUser for more hints.
    
}

function handleDeleteExercise(event){
    if (DEBUG) {
        console.log ("Triggered handleDeleteExercise");
    }
    var exerciseurl = $(this).closest("form").attr("action");
    delete_message(exerciseurl);    
    //TODO 2:
    //  Extract the url of the resource to be deleted from the form action attribute.
    //  Call the method delete_message(messageurl).
    //  Check handleDeleteUser for more hints.
    
}
//own stuff
function handleSearchUser(event) {
    if (DEBUG) {
        console.log ("Triggered handleSearchUser");
    }
    event.preventDefault();

    prepareUserDataVisualization();
	
	console.log ("/exercisetracker/api/users/"+$("#search_field").find('input[name="search_field_text"]').val());
    
	get_user("/exercisetracker/api/users/"+$("#search_field").find('input[name="search_field_text"]').val());
 
   
    return false; //IMPORTANT TO AVOID <A> BUBLING
}
function handleAddExercise(event) {
    if (DEBUG) {
        console.log ("Triggered handleAddExercise");
    }
    event.preventDefault();

    //prepareUserDataVisualization();
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
	//createFormFromSchema("/exercisetracker/api/exercises/", "add-exer.schema", "add_exercise_form");
   //add username to form

    return false; //IMPORTANT TO AVOID <A> BUBLING
}


function handleSubmitAddExercise(event){
    if (DEBUG) {
        console.log ("Triggered handleSubmitAddExercise");
    }
    event.preventDefault();

    var $form = $(this).closest("form");
    var template = serializeFormTemplate($form);
    var url = $form.attr("action");

    //template is missing userid. otherwise functioning
    add_exercise(url, template);
    return false; //Avoid executing the default submit    
}

function handleRemoveExercise(event){
    if (DEBUG) {
        console.log ("Triggered handleRemoveExercise");
    }
    event.preventDefault();
	console.log($(this).attr("href"));
	remove_exercise($(this).attr("href"));

    return false; //Avoid executing the default submit    
}

function handleRemoveUser(event){
    if (DEBUG) {
        console.log ("Triggered handleRemoveUser");
    }
    event.preventDefault();
	console.log($(this).attr("href"));
	remove_user($(this).attr("href"));

    return false; //Avoid executing the default submit    
}

//
/**** END BUTTON HANDLERS ****/

/*** START ON LOAD ***/
//This method is executed when the webpage is loaded.
$(function(){
    $("#addUserButton").on("click", handleShowUserForm);
    $("#deleteUser").on("click", handleDeleteUser);
    $("#editUser").on("click", handleEditUser);
    $("#deleteUserRestricted").on("click", handleDeleteUserRestricted);
    $("#editUserRestricted").on("click", handleEditUserRestricted);
    $("#createUser").on("click", handleCreateUser);
	$("#add_friend_href").on("click", handleAddFriend);
    
    $(".deleteMessage").on("click", handleDeleteMessage);
    $("#deleteExercise").on("click", handleDeleteExercise);
    $("#user_list").on("click","li a" ,handleGetUser);

//own additions
	$("#search_button").on("click",handleSearchUser);
	$("#add_exercise_button").on("click",handleAddExercise);
    $("#friend_list").on("click","li a" ,handleGetUser);
    $("#remove_friend_list").on("click","li a" ,handleRemoveFriend);

    $("#addExercise").on("click",handleSubmitAddExercise);
    $("#remove_exercise_button").on("click",handleRemoveExercise);
    $("#exercise_list").on("click","li a" ,handleGetExercise);

    $("#remove_user_button").on("click",handleRemoveUser);
	
	//startup sequence. Creates schemas etc
	startup(ENTRYPOINT);
	//$("#mainContent").hide();
//


    
    //TODO 1: Add corresponding click handlers for .deleteMessage button and
    // #user_list li a anchors. Since these elements are generated dynamically
    // (they are not in the initial HTML code), you must use delegated events.
    // Recommend delegated elements are #messages_list for .deleteMessage buttons and
    // #user_list for "#user_list li a" anchors.
    // The handlers are:
    // .deleteMessage => handleDeleteMessage
    // #user_list li a => handleGetUser
    // More information for direct and delegated events from http://api.jquery.com/on/
    

    


});
/*** END ON LOAD**/
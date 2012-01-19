/*
 *  Genric Model
 *  
 *  args:
 *    * obj: the object this model represents
 *  
 *  methods:
 *    * deleteObject: Delete the model
 */
var Model = function(obj, csrftoken) {
    this.name = ko.observable(obj.name);
    this.title = this.name().replace(/_/gi, ' ');
    this.formVisible = ko.observable(false);
    this.csrftoken = csrftoken;

    this.toggleForm = function() {
        this.formVisible(!this.formVisible());
    };

    this.deleteObject = function() {
        jQuery.ajax({
            url : this.url,
            type : 'DELETE',
            data : {csrfmiddlewaretoken: this.csrftoken},
            success : $.proxy(function(data) {
                if(this.onDelete) {
                    this.onDelete(this);
                }
            }, this)
        });
    };
};

var Group = function(obj, csrftoken) {
    jQuery.proxy(Model, this)(obj, csrftoken);
    this.absolute_url = '/' + this.name() + '/';
    this.description = ko.observable(obj.description);
    this.url = '/_api/groups/' + this.name();
};

var Project = function(obj, csrftoken) {
    jQuery.proxy(Model, this)(obj, csrftoken);
    this.group = obj.group
    this.description = ko.observable(obj.description)
    this.absolute_url = '/' + obj.group + '/' + this.name() + '/';
    this.url = '/_api/projects/' + this.name();
};

var Key = function(obj, csrftoken) {
    jQuery.proxy(Model, this)(obj, csrftoken);
    this.working = ko.observable(false);
    this.name = ko.observable(obj.name);
    this.key = ko.observable(obj.ssh_key);
    this.url = '/_api/keys/' + this.name();
    this.errors = ko.observable();
    this.csrftoken = csrftoken;
    this.editFormVisible = ko.observable(false);
    
    this.toggleEditForm = function() {
        this.editFormVisible(!this.editFormVisible());
    };
    
    this.resetForm = function() {
        this.editFormVisible(false);
        this.errors('');
    };
    
    this.editOptions = function() {
        console.log(this.csrftoken);
        return {
            csrfmiddlewaretoken: this.csrftoken,
            name: this.name(),
            ssh_key: this.key()
        }; 
    };
    
    this.editObject = function(formElement) {
        jQuery.ajax({
            url : this.url,
            type : 'POST',
            data : this.editOptions(),
            success : $.proxy(function(data) {
                if(data.errorMsg) {
                    this.errors(data.errorMsg);
                } else {
                    this.resetForm();
                }
            }, this),
            error : $.proxy(function(data) {
                console.log(data);
                this.errors(data);
            }, this),
            complete : $.proxy(function() {
                this.working(false);
            }, this)
        });
    };
};

/*
 *  Generic Collection
 *  
 *  methods:
 *   * fetch: grab all objects for user.
 *   * extractData: pull the data from the api call and create
 *                  this.model objects with the data.
 */
var Collection = function(csrftoken) {
    // Fetching objects for the collection
    this.working = ko.observable(false);
    this.items = ko.observableArray([]);
    this.csrftoken = csrftoken;
    this.options = {};
    this.url = '';
    this.model = null;
    
    // Callback for when a item is deleted    
    this.itemDeleted = function(item) {
        this.items.remove(item);
    };
    
    // Callback for new object creation form data
    this.newOptions = function () {
        return {csrfmiddlewaretoken: this.csrftoken};
    };
    
    // Extract data and enrich it with model object
    this.extractData = function(data) {
        if (data.objects) {
            if (this.model) {
                var objs = data.objects;
                ko.utils.arrayForEach(objs, jQuery.proxy(function(obj) {
                    jQuery.extend(obj, new this.model(obj, this.csrftoken));
                    obj.onDelete = jQuery.proxy(this.itemDeleted, this);
                }, this));
                return data.objects;
            }
            return data.objects;
        }
        return [];
    };
    
    
    this.addObject = function(formElement) {
        this.working(true);

        jQuery.ajax({
            url : this.url,
            type : 'POST',
            data : this.newOptions(),
            success : $.proxy(function(data) {
                if(data.errorMsg) {
                    this.errors(data.errorMsg);
                } else {
                    var obj = new this.model(data);
                    obj.onDelete = jQuery.proxy(this.itemDeleted, this);
                    this.items.push(obj);
                    this.resetForm();
                }
            }, this),
            error : $.proxy(function(data) {
                console.log(data);
                this.errors(data);
            }, this),
            complete : $.proxy(function() {
                this.working(false);
            }, this)
        });
    };
    
    // Grab list of objects
    this.fetch = function() {
        this.working(true);

        jQuery.ajax({
            url : this.url,
            type : 'GET',
            dataType : 'json',
            data : this.options,
            success : $.proxy(function(data) {
                var newItems = this.extractData(data) || [];
                var items = this.items();
                $.merge(items, newItems);
                this.items(items);
            }, this),
            complete : $.proxy(function() {
                this.working(false);
            }, this)
        });
    };
    
}

var GroupCollection = function(csrftoken) {
    jQuery.proxy(Collection, this)(csrftoken);
    this.url = '/_api/groups/';
    this.name = ko.observable('');
    this.description = ko.observable('');
    this.errors = ko.observable();
    this.formVisible = ko.observable(false);
    this.model = Group;
    
    this.newOptions = function () {
        return {
            csrfmiddlewaretoken: this.csrftoken,
            name: this.name(),
            description: this.description() 
        };
    };

    this.resetForm = function() {
        this.name('');
        this.description('');
        this.formVisible(false);
        this.errors('');
    };

    this.toggleForm = function() {
        this.formVisible(!this.formVisible());
    };
    
    // Grab the initial groups
    this.fetch();
    
};

var ProjectCollection = function(groupName, csrftoken) {
    jQuery.proxy(Collection, this)(csrftoken);
    this.url = '/_api/projects/';
    this.options = {group: groupName};
    this.name = ko.observable('');
    this.description = ko.observable('');
    this.errors = ko.observable();
    this.formVisible = ko.observable(false);
    this.model = Project;
    
    this.newOptions = function () {
        return {
            name: this.name(),
            description: this.description(),
            group: groupName,
            csrfmiddlewaretoken: this.csrftoken
        };
    };
    
    this.resetForm = function() {
        this.name('');
        this.description('');
        this.formVisible(false);
        this.errors('');
    };

    this.toggleForm = function() {
        this.formVisible(!this.formVisible());
    };
    
    // Grab the initial groups
    this.fetch();
    
};

var KeyCollection = function(csrftoken) {
    jQuery.proxy(Collection, this)(csrftoken);
    this.url = '/_api/keys/';
    this.name = ko.observable('');
    this.key = ko.observable('');
    this.errors = ko.observable();
    this.formVisible = ko.observable(false);
    this.model = Key;
    
    this.newOptions = function () {
        return {
            name: this.name(),
            ssh_key: this.key(),
            csrfmiddlewaretoken: this.csrftoken
        };
    };
    
    this.resetForm = function() {
        this.name('');
        this.key('');
        this.formVisible(false);
        this.errors('');
    };

    this.toggleForm = function() {
        this.formVisible(!this.formVisible());
    };
    
    // Grab the initial groups
    this.fetch();
    
};

// Here's a custom Knockout binding that makes elements shown/hidden via jQuery's fadeIn()/fadeOut() methods
// Could be stored in a separate utility library
ko.bindingHandlers.fadeVisible = {
    init: function(element, valueAccessor) {
        // Initially set the element to be instantly visible/hidden depending on the value
        var value = valueAccessor();
        $(element).toggle(ko.utils.unwrapObservable(value)); // Use "unwrapObservable" so we can handle values that may or may not be observable
    },
    update: function(element, valueAccessor) {
        // Whenever the value subsequently changes, slowly fade the element in or out
        var value = valueAccessor();
        ko.utils.unwrapObservable(value) ? $(element).fadeIn() : $(element).fadeOut();
    }
};

/* ============================================================
 * bootstrap-dropdown.js v1.3.0
 * http://twitter.github.com/bootstrap/javascript.html#dropdown
 * ============================================================
 * Copyright 2011 Twitter, Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 * ============================================================ */


!function( $ ){

  /* DROPDOWN PLUGIN DEFINITION
   * ========================== */

  $.fn.dropdown = function ( selector ) {
    return this.each(function () {
      $(this).delegate(selector || d, 'click', function (e) {
        var li = $(this).parent('li')
          , isActive = li.hasClass('open')

        clearMenus()
        !isActive && li.toggleClass('open')
        return false
      })
    })
  }

  /* APPLY TO STANDARD DROPDOWN ELEMENTS
   * =================================== */

  var d = 'a.menu, .dropdown-toggle'

  function clearMenus() {
    $(d).parent('li').removeClass('open')
  }

  $(function () {
    $('html').bind("click", clearMenus)
    $('body').dropdown( '[data-dropdown] a.menu, [data-dropdown] .dropdown-toggle' )
  })

}( window.jQuery || window.ender );

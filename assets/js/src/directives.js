'use strict';

/* Directives */


angular.module('myApp.directives', []).
  directive('whenScrolled', function() {
    return function(scope, elm, attr) {
        var raw = elm[0];
        
        elm.bind('scroll', function() {
            if (raw.scrollTop + raw.offsetHeight >= raw.scrollHeight) {
                scope.$apply(attr.whenScrolled);
            }
        });
    };
  }).
  directive('loginForm', function() {
  	return {
	  	restrict: 'C',
	  	link: function(scope, elm, attr) {
	  	var el = $(elm[0]);
	  	scope.$on('event:auth-loginRequired', function() {
	  	  el.modal('show');
	  	});
	    scope.$on('event:auth-loginConfirmed', function() {
	 	  el.modal('hide');
	  	});
  	  }
  	}
  });
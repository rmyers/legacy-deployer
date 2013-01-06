'use strict';

/* Directives */


angular.module('myApp.directives', ['http-auth-interceptor']).
  directive('appVersion', ['version', function(version) {
    return function(scope, elm, attrs) {
      elm.text(version);
    };
  }]);

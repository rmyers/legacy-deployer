'use strict';

/* Controllers */

function MainCntl($scope, $route, $routeParams, $location, User) {
  $scope.$route = $route;
  $scope.$location = $location;
  $scope.$routeParams = $routeParams;
  $scope.account = User;
}

function IndexController($scope) {
	$scope.page = 'index'
}



function SignupController($scope, $http, authService, $window, User) {
  $scope.page = 'signup';
  $scope.account = User;
  $scope.submit = function () {
    if ($scope.password != $scope.confirm) {
      $scope.error = "Passwords do not match!";
    } else {
      $http.post('/accounts/signup/', jQuery.param($scope.user), {
        headers: {'Content-Type': 'application/x-www-form-urlencoded'}
      }).
      success(function(data) {
        authService.loginConfirmed();
        $scope.username = '';
        $scope.password = '';
        $scope.error = false;
        $scope.account = data;
        // Reload the page from the server
        $window.location.href = '/dashboard';
      }).
      error(function(resp) {
        $scope.error = resp.message;
      });
    }
  };
}

function SignupControllerResolve($q) {
  var delay = $q.defer();
  alert('delay');
  setTimeout(delay.resolve, 5000);
  return delay.promise;
};

function DashboardController($resource, $scope, Group, Project) {
  Project.query({}, function(data){
    $scope.projects = data.models;
  });
  Group.query({}, function(data){
  	$scope.groups = data.models;
  });
  $scope.submit = function () {
  	var new_project = new Project($scope.project);
  	new_project.$save();
  	$scope.projects.push(new_project);
  };
  
}

function ProjectController($resource, $scope, $route, $routeParams, User, Project) {
  console.log('boo');
  $scope.account = User;
  Project.query({}, function(data){
  	$scope.projects = data.models;
  });
  console.log($routeParams);
  if ($routeParams.projectId) {
  	$scope.myProject = Project.get({projectId: $routeParams.projectId});
  }
  $scope.submit = function () {
  	var new_project = new Project($scope.project);
  	new_project.$save();
  	$scope.projects.push(new_project);
  };
}

function PeopleController($resource, $scope, People) {
  People.query({}, function(data){
    $scope.users = data.models;
  });
}

function LoginController($scope, $http, authService, $window, User) {
  $scope.page = 'signup';
  $scope.account = User;
  $scope.submit = function () {
    console.log($scope.account);
    $http.post('/accounts/signin/', jQuery.param($scope.user), {
      headers: {'Content-Type': 'application/x-www-form-urlencoded'}
    }).
    success(function(resp) {
      console.log(resp);
      authService.loginConfirmed();
      $scope.error = false;
      $scope.account = resp;
      $window.location.href = '/dashboard';
    }).
    error(function(resp) {
      $scope.error = resp.message;
    });
  };
}

MainCntl.$inject = ['$scope', '$route', '$routeParams', '$location', 'People'];
DashboardController.$inject = ['$resource', '$scope', 'Group', 'Project'];
LoginController.$inject = ['$scope', '$http', 'authService', '$window', 'User'];
PeopleController.$inject = ['$resource', '$scope', 'People'];
SignupController.$inject = ['$scope', '$http', 'authService', '$window', 'User'];
IndexController.$inject = ['$scope', 'User'];
ProjectController.$inject = ['$resource', '$scope', '$route', '$routeParams', 'User', 'Project'];

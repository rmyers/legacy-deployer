
var deps = [
  'js/vendor/**/*.js',
];

var apps = [
	'js/src/**/*.js'
];

module.exports = function(grunt) {

  grunt.initConfig({
    lint: {
      files: ['grunt.js', 'js/src/**/*.js', 'js/spec/**/*.js']
    },

    // Dev-mode - just concatenate our js files
    concat: {
      app: {
        src: apps,
        dest: '../cannula/static/js/app.js'
      },
      vendor: {
        src: deps,
        dest: '../cannul/static/js/vendor.js'
      }
    },

    // Production-mode - minify app and vendor
    min: {
      app: {
	    src: apps,
        dest: '../cannula/static/js/app.js'
      },
      vendor: {
        src: deps,
        dest: '../cannula/static/js/vendor.js'
      }
    },

    // less compilation
    less: {
      dev: {
        options: {
            paths: ["assets/bootstrap/less"]
        },
        files: {
            "../cannula/static/css/main.css": "less/layout.less"
        }
      },
      prod: {
        options: {
            paths: ["assets/bootstrap/less"],
            compress: true            
        },
        files: {
            "../cannula/static/css/main.css": "less/layout.less"
        }
      }
    },
	
	copy: {
	  dist: {
	  	files: {
	  	  "../cannula/static/img/": "bootstrap/img/*",
	  	  "../cannula/static/img/": "img/*"
	  	}
	  }
	},
	
    // Watch tasks for development
    watch: {
      less: {
        files: 'less/*.less',
        tasks: 'less:dev'
      },

      js: {
        files: 'js/src/**/*.js',
        tasks: 'concat:app'
      },

      vendor: {
        files: 'js/vendor/**/*.js',
        tasks: 'concat:vendor'
      }
    },

    // Run our Jasmine tests
    jasmine: {
      src: deps.concat(apps),
      specs: 'js/spec/**/*Spec.js',
      junit: {
        output: 'junit/'
      }
    }

  });

  grunt.loadNpmTasks('grunt-jasmine-runner');
  grunt.loadNpmTasks('grunt-contrib-less');
  grunt.loadNpmTasks('grunt-contrib-copy');
};

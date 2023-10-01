/** @type {import('tailwindcss').Config} */


const withMT = require("@material-tailwind/html/utils/withMT");
 
module.exports = withMT({
  content: ["./templates/**/*.html", "./**/*.py", "./static/**/*.{css,html,js}"],
  theme: {
    extend: {
      colors : {
        'primary' : {
          '300': '#ff3537',
          '400': '#e12e31',
          '500': '#bb2729',
          '600': '#871c1d',
          '700': '#6e1718',
        },
        'secondary' : {
          '300': '#253d91',
          '400': '#1b2d6b',
          '500': '#121d45',
          '600': '#040811',
          '700': '#000000',
        },
        'tertiary' : {
          '300': '#ff6f59',
          '400': '#ff5959',
          '500': '#d94c4d',
          '600': '#a53a3a',
          '700': '#8c3131',
        },
        'light' : {
          '300': '#ffecda',
          '400': '#ffeccc',
          '500': '#f6dec5',
          '600': '#c3af9c',
          '700': '#a99887',
        },
        },
    },

  },
  plugins: [],
});
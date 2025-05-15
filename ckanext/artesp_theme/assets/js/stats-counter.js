/**
 * Stats Counter Animation
 * 
 * This script animates the statistics counters on the homepage,
 * incrementing from 0 to the final value when the stats section
 * comes into view.
 */

(function() {
  // Function to check if an element is in the viewport
  function isInViewport(element) {
    const rect = element.getBoundingClientRect();
    return (
      rect.top <= (window.innerHeight || document.documentElement.clientHeight) &&
      rect.bottom >= 0
    );
  }

  // Function to animate counter from 0 to target value
  function animateCounter(element, targetValue) {
    // Parse the target value as an integer
    const target = parseInt(targetValue, 10);
    
    // If the target is not a valid number, exit
    if (isNaN(target)) return;
    
    // Set the duration of the animation in milliseconds
    const duration = 2000;
    
    // Calculate the increment per step
    const increment = target / (duration / 16);
    
    // Initialize the current value
    let currentValue = 0;
    
    // Start the animation
    const timer = setInterval(() => {
      // Increment the current value
      currentValue += increment;
      
      // If the current value exceeds the target, set it to the target
      if (currentValue >= target) {
        clearInterval(timer);
        element.textContent = target;
      } else {
        // Update the element with the current value (rounded to an integer)
        element.textContent = Math.floor(currentValue);
      }
    }, 16);
  }

  // Function to initialize the counter animation
  function initCounters() {
    // Get all stat count elements
    const statCounts = document.querySelectorAll('.stat-count');
    
    // Flag to track if animation has been triggered
    let animated = false;
    
    // Function to check if stats section is in view and trigger animation
    function checkAndAnimate() {
      // If already animated, exit
      if (animated) return;
      
      // Get the stats section
      const statsSection = document.querySelector('.stats-section');
      
      // If stats section exists and is in viewport
      if (statsSection && isInViewport(statsSection)) {
        // Set animated flag to true
        animated = true;
        
        // Animate each counter
        statCounts.forEach(counter => {
          // Get the target value from the element's text content
          const targetValue = counter.textContent;
          
          // Set initial value to 0
          counter.textContent = '0';
          
          // Start the animation
          animateCounter(counter, targetValue);
        });
        
        // Remove the scroll event listener once animation is triggered
        window.removeEventListener('scroll', checkAndAnimate);
      }
    }
    
    // Add scroll event listener
    window.addEventListener('scroll', checkAndAnimate);
    
    // Check if stats section is already in view on page load
    checkAndAnimate();
  }

  // Initialize the counters when the DOM is fully loaded
  document.addEventListener('DOMContentLoaded', initCounters);
})();

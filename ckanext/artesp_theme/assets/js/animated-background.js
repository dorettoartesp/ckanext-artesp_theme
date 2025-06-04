/**
 * Animated SVG Background for Hero Section
 *
 * Features multiple transportation modals moving randomly.
 */
(function() {
  'use strict';

  const SVG_NAMESPACE = 'http://www.w3.org/2000/svg';
  const XLINK_NAMESPACE = 'http://www.w3.org/1999/xlink';

  // Configuration for single vehicle mode
  const RUN_SINGLE_VEHICLE_MODE = true; // Set to true to run only one vehicle
  const GLOBAL_VEHICLE_Y_FACTOR = 0.71; // Vertical position factor for ALL vehicles (0.0 = top, 1.0 = bottom)
                                        // This factor determines the vertical center of the vehicle.
 const vehicleTypes = [
    {
      type: 'airplane',
      id: 'airplane-def',
      count: 3,
      minSpeed: 0.4, maxSpeed: 1.2,
      baseWidth: 33, baseHeight: 22.5, // From hero-background-defs.svg comments
      xOffset: 0, yOffset: 0,
      allowFlip: false, // Rotation handles direction
    },
    {
      type: 'car',
      id: 'car-def',
      count: 6,
      minSpeed: 0.8, maxSpeed: 2.0,
      baseWidth: 30, baseHeight: 18,
      xOffset: 0, yOffset: 0,
      zoneYStartFactor: 0.65, zoneYEndFactor: 0.9,
      allowFlip: true,
      colors: ['#E74C3C', '#3498DB', '#2ECC71', '#F1C40F', '#9B59B6', '#34495E']
    },
    {
      type: 'bus',
      id: 'bus-def',
      count: 2,
      minSpeed: 0.6, maxSpeed: 1.5,
      baseWidth: 50, baseHeight: 24,
      xOffset: 0, yOffset: 0,
      zoneYStartFactor: 0.6, zoneYEndFactor: 0.85,
      allowFlip: true,
    },
    {
      type: 'subway',
      id: 'subway-def',
      count: 1,
      minSpeed: 1.0, maxSpeed: 1.8,
      baseWidth: 90, baseHeight: 20, // Visual height including bogies
      xOffset: 0, yOffset: 5,       // Drawing starts 5 units down from <g> origin
      zoneYStartFactor: 0.75, zoneYEndFactor: 0.78, // Narrower band for tracks
      allowFlip: true,
    },
    {
      type: 'ferry',
      id: 'ferry-boat-def',
      count: 1,
      minSpeed: 0.2, maxSpeed: 0.6,
      baseWidth: 60, baseHeight: 25, // Total visual height
      xOffset: 0, yOffset: -5,      // Part of drawing (deckhouse) extends above <g> origin
      zoneYStartFactor: 0.85, zoneYEndFactor: 0.95, // Water area
      allowFlip: true,
    }
  ];

  let svg;
  let svgWidth, svgHeight; // Will be set after SVG is found
  const vehicles = [];
  let animationFrameId = null; // To store the request ID for canceling

  function getRandom(min, max) {
    return Math.random() * (max - min) + min;
  }

  function createVehicle(config) {
    const vehicle = { ...config }; // Clone config
    let element;

    if (config.type === 'car') {
      // Find the definition within the main SVG's defs
      const originalGroup = svg.querySelector(`#${config.id}`);
      if (!originalGroup) {
        console.error(`SVG definition not found for ID: ${config.id}`);
        return null;
      }
      element = originalGroup.cloneNode(true);
      element.removeAttribute('id'); // Avoid duplicate IDs in DOM
      const carBody = element.querySelector('.car-body');
      if (carBody && config.colors && config.colors.length > 0) {
        const randomColor = config.colors[Math.floor(Math.random() * config.colors.length)];
        carBody.setAttribute('fill', randomColor);
      }
    } else {
      // Find the definition within the main SVG's defs for <use> elements
      const defExists = svg.querySelector(`#${config.id}`);
      if (!defExists) {
          console.error(`SVG definition not found for ID: ${config.id} (for <use>)`);
          return null;
      }
      element = document.createElementNS(SVG_NAMESPACE, 'use'); // Create the <use> element
      element.setAttributeNS(XLINK_NAMESPACE, 'href', `#${config.id}`);
    }
    
    vehicle.element = element;
    svg.appendChild(element);
    resetVehicleState(vehicle, true);
    return vehicle;
  }

  function resetVehicleState(vehicle, isInitial = false) {
    vehicle.speed = getRandom(vehicle.minSpeed, vehicle.maxSpeed);

    // Calculate the target Y position for the visual center of the vehicle
    const targetCenterY = GLOBAL_VEHICLE_Y_FACTOR * svgHeight;
    // Calculate the vehicle's y coordinate (top-left corner of its group/use element)
    // so that its visual center aligns with targetCenterY
    const vehicleVisualTopY = targetCenterY - (vehicle.baseHeight / 2);
    vehicle.y = vehicleVisualTopY - vehicle.yOffset; // Adjust for yOffset

    if (vehicle.type === 'airplane') {
      vehicle.vy = 0; // Strictly horizontal movement

      // Determine direction: LTR or RTL
      const moveLTR = Math.random() < 0.5;
      if (moveLTR) { // Moving Left-to-Right
        vehicle.vx = vehicle.speed; // Move right
        vehicle.angle = 0; // No rotation needed to face right (matches SVG orientation)
        vehicle.x = -vehicle.baseWidth - vehicle.xOffset - getRandom(0, svgWidth * 0.1);
      } else { // Moving Right-to-Left
        vehicle.vx = -vehicle.speed; // Move left
        vehicle.angle = 180; // Rotate 180 degrees to face left
        vehicle.x = svgWidth - vehicle.xOffset + getRandom(0, svgWidth * 0.1);
      }

      // Airplanes fly straight horizontally at the target Y
      vehicle.baseY = vehicle.y; // Base Y is the fixed Y
      vehicle.curveAmplitude = 0; // No vertical oscillation
      vehicle.curveFrequency = 0;
      vehicle.curvePhase = 0;
    } else { // Horizontal movers (car, bus, subway, ferry)
      vehicle.vy = 0;
      vehicle.scaleX = (vehicle.allowFlip && Math.random() < 0.5) ? -1 : 1;
      vehicle.vx = vehicle.speed * vehicle.scaleX;

      if (vehicle.vx > 0) { // Moving LTR
        vehicle.x = -vehicle.baseWidth - vehicle.xOffset - getRandom(0, svgWidth * 0.3);
      } else { // Moving RTL
        vehicle.x = svgWidth - vehicle.xOffset + getRandom(0, svgWidth * 0.3);
      }
    }
  }

  function updateVehicleTransform(vehicle) {
    let transform = '';
    const visualCenterX = vehicle.xOffset + vehicle.baseWidth / 2;
    const visualCenterY = vehicle.yOffset + vehicle.baseHeight / 2;

    if (vehicle.type === 'airplane') {
      transform = `translate(${vehicle.x}, ${vehicle.y}) rotate(${vehicle.angle}, ${visualCenterX}, ${visualCenterY})`;
    } else { // Horizontal movers
      if (vehicle.scaleX === -1) {
        transform = `translate(${vehicle.x}, ${vehicle.y}) translate(${visualCenterX}, ${visualCenterY}) scale(-1, 1) translate(${-visualCenterX}, ${-visualCenterY})`;
      } else {
        transform = `translate(${vehicle.x}, ${vehicle.y})`;
      }
    }
    vehicle.element.setAttribute('transform', transform);
  }

  // Function to create and add a single random vehicle
  function createRandomSingleVehicle() {
    // Select a random vehicle type configuration
    const config = vehicleTypes[Math.floor(Math.random() * vehicleTypes.length)];

    if (config) {
      const vehicle = createVehicle(config); // createVehicle makes one instance
      if (vehicle) {
        vehicles.push(vehicle); // Add the new vehicle to the array
      }
    } else {
      console.error(`Could not select a random vehicle type configuration.`);
    }
  }

  function animate() {
    // Iterate backwards to allow safe removal from the array while iterating
    for (let i = vehicles.length - 1; i >= 0; i--) {
      const vehicle = vehicles[i];

      vehicle.x += vehicle.vx;

      if (vehicle.type === 'airplane') {
        // Apply curvy path for airplanes
        vehicle.y = vehicle.baseY +
                    vehicle.curveAmplitude * Math.sin(vehicle.curveFrequency * vehicle.x + vehicle.curvePhase);
      } else {
        // Other vehicles maintain their y (or would change if vy was non-zero)
        vehicle.y += vehicle.vy;
      }

      let isOutOfBounds = false;
      const visualX = vehicle.x + vehicle.xOffset; // Effective left edge on screen
      const offScreenBuffer = vehicle.baseWidth;

      if (vehicle.vx > 0) { // Moving LTR
        isOutOfBounds = visualX > svgWidth + offScreenBuffer;
      } else { // Moving RTL (vx < 0)
        isOutOfBounds = (visualX + vehicle.baseWidth) < -offScreenBuffer;
      }
      
      if (isOutOfBounds) {
        const currentVehicleType = vehicle.type;

        // Remove the old vehicle
        svg.removeChild(vehicle.element);
        vehicles.splice(i, 1); // Remove vehicle from array

        // Select a new, preferably different, vehicle type
        let potentialNewTypes = vehicleTypes.filter(vt => vt.type !== currentVehicleType);

        if (potentialNewTypes.length === 0 && vehicleTypes.length > 0) {
          // Fallback: if only one type exists or filtering failed to find a *different* one.
          // In this case, pick from any available type.
          console.warn(`Could not select a *different* vehicle type than '${currentVehicleType}'. Either only one type is defined, or an issue occurred. A random type will be selected from all available types.`);
          potentialNewTypes = vehicleTypes;
        }

        if (potentialNewTypes.length > 0) {
          const newConfig = potentialNewTypes[Math.floor(Math.random() * potentialNewTypes.length)];
          const newVehicle = createVehicle(newConfig); // createVehicle also calls resetVehicleState
          if (newVehicle) {
            vehicles.push(newVehicle); // Add the new vehicle to the array
          }
        } else {
          console.error("No vehicle types available to create a replacement vehicle.");
        }
      } else {
        updateVehicleTransform(vehicle);
      }
    }

    animationFrameId = requestAnimationFrame(animate);
  }

  function init() {
    svg = document.getElementById('animated-background-svg');
    if (!svg) {
      console.error('Animated SVG background element not found.');
      return;
    }

    const defsSrc = svg.dataset.defsSrc;
    if (!defsSrc) {
      console.error('SVG definitions source URL not found (data-defs-src attribute missing).');
      return;
    }

    fetch(defsSrc)
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.text();
      })
      .then(defsContent => {
        const parser = new DOMParser();
        // Wrap content in <svg> tags to provide a valid root element for parsing.
        // This is crucial because hero-background-defs.svg contains multiple <g> elements directly.
        const wrappedDefsContent = `<svg xmlns="${SVG_NAMESPACE}">${defsContent}</svg>`;
        const doc = parser.parseFromString(wrappedDefsContent, 'image/svg+xml');

        const parserError = doc.querySelector('parsererror');
        if (parserError) {
            console.error('SVG parsing error:', parserError.textContent);
            throw new Error('Failed to parse fetched SVG content due to syntax errors.');
        }

        let defsElement = svg.querySelector('defs');
        if (!defsElement) {
            defsElement = document.createElementNS(SVG_NAMESPACE, 'defs');
            svg.prepend(defsElement); // Add the new <defs> to the main SVG
        }

        // doc.documentElement will be the temporary <svg> wrapper we created.
        // Its children are the <g> elements we want.
        const parsedDefsContainer = doc.documentElement;
        while (parsedDefsContainer.firstChild) {
            // Appends each <g> from the parsed content into the main SVG's <defs>
            defsElement.appendChild(parsedDefsContainer.firstChild);
        }

        // --- Definitions are now in the DOM ---

        svgWidth = svg.viewBox.baseVal.width;
        svgHeight = svg.viewBox.baseVal.height;

        if (RUN_SINGLE_VEHICLE_MODE) {
          // Create the initial random single vehicle
          createRandomSingleVehicle();
        } else {
          // Original multi-vehicle creation logic
          vehicleTypes.forEach(config => {
            for (let i = 0; i < config.count; i++) {
              const vehicle = createVehicle(config);
              if (vehicle) {
                vehicles.push(vehicle);
              }
            }
          });
        }

        if (vehicles.length > 0) {
          animate();
        }

        // Add mouse event listeners for interaction
        svg.addEventListener('mouseenter', () => {
            if (animationFrameId) {
                cancelAnimationFrame(animationFrameId);
                animationFrameId = null;
                // console.log('Animation paused'); // Optional: for debugging
            }
        });

        svg.addEventListener('mouseleave', () => {
            if (!animationFrameId) { // Only restart if it's currently paused
                // console.log('Animation resumed'); // Optional: for debugging
                animate();
            }
        });
      })
      .catch(error => console.error('Error loading or parsing SVG definitions:', error));
  }
  
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    // DOMContentLoaded has already fired
    init();
  }
})();

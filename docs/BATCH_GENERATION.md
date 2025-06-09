# Batch Generation Feature

## Overview
The batch generation feature allows users to generate multiple images with variations from a single prompt. This is useful for exploring different interpretations of the same concept.

## Features
- Generate 1-4 images at once with a single prompt
- Each image receives a unique variation modifier
- Progress tracking during generation
- Individual actions for each generated image:
  - Save to gallery
  - Share via Android intent
  - View in full screen

## How to Use
1. Navigate to the main screen of the app
2. Scroll down to find the "Batch Generation" section
3. Enter your desired prompt in the batch prompt field
4. Use the slider to select how many images to generate (1-4)
5. Tap the "Generate Batch" button
6. Wait for the images to generate - progress updates will appear
7. Once generated, each image will appear in the grid with action buttons

## Technical Details

### UI Components (ui/main_screen.kv)
- `batch_prompt`: TextField for entering the prompt
- `batch_slider`: Slider for selecting number of images (1-4)
- `batch_grid`: GridLayout that displays generated images
- "Generate Batch" button to start the process

### Backend Implementation (screens/main_screen.py)
- `generate_batch()`: Main method that initiates batch generation
- `_generate_batch_thread()`: Background thread that generates images
- `_add_batch_image()`: Adds each generated image to the UI grid
- `_save_batch_image()`: Saves batch image to gallery
- `_share_batch_image()`: Shares batch image via Android
- `_view_batch_image()`: Opens image in full-screen viewer
- `_complete_batch_generation()`: Shows completion status

### Variation System
The batch generation uses predefined variations to create diverse outputs:
- "artistic style"
- "different perspective"
- "vibrant colors"
- "dramatic lighting"
- "unique composition"
- "alternative view"

## API Usage
Each batch generation makes separate API calls to DALL-E 2, so generating 4 images will use 4 API credits.

## Error Handling
- Progress tracking shows successful and failed generations
- Failed images are counted and reported in the completion message
- Each image generation failure is handled independently

## Future Enhancements
- Add ability to save all batch images at once
- Implement custom variation prompts
- Add batch generation history
- Support for larger batch sizes (premium feature)

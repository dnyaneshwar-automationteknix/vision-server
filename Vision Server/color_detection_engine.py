"""
Complete Color Detection System - Android-style Implementation in Python
Supports: Bounding Boxes, Rings, ROI, RGB Range Matching
"""

import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional
import json
import math


class ColorDetectionEngine:
    """
    Complete color detection engine matching Android functionality
    Supports:
    - Bounding box color detection (similar to BoundingBoxTableCD)
    - Ring-based color detection (similar to Ring)
    - Pixel-by-pixel RGB range matching
    - Multiple color ranges (C1, C2)
    - Pitch counting and pattern detection
    """
    
    def __init__(self):
        self.results_cache = []
    
    # ==================== BOUNDING BOX DETECTION ====================
    
    def detect_colors_in_boxes(self, image: np.ndarray, boxes: List[Dict], 
                               image_ratio: float = 1.0) -> List[Dict]:
        """
        Detect colors in bounding boxes - Android getResultsForBoxes equivalent
        
        Args:
            image: BGR image (numpy array)
            boxes: List of box definitions with RGB ranges
            image_ratio: Ratio between captured and preview image
            
        Box format:
        {
            'id': 1,
            'model_id': 'CD',
            'position': 1,
            'left': 100,
            'right': 200,
            'top': 50,
            'bottom': 150,
            'c1_r_from': 0, 'c1_g_from': 0, 'c1_b_from': 0,
            'c1_r_to': 50, 'c1_g_to': 50, 'c1_b_to': 50,
            'c2_r_from': 200, 'c2_g_from': 200, 'c2_b_from': 200,
            'c2_r_to': 255, 'c2_g_to': 255, 'c2_b_to': 255,
            'c1_pixel_count_range': 10,
            'c2_pixel_count_range': 10,
            'pixel_range': 50.0,
            'greater_less_than': 'GREATER_THAN',
            'ok_nok': 'OK'
        }
        
        Returns: List of ColorDetectionResult
        """
        results = []
        
        if len(boxes) == 0:
            return results
        
        height, width = image.shape[:2]
        
        for box in boxes:
            result = self._process_single_box(image, box, image_ratio)
            results.append(result)
        
        return results
    
    def _process_single_box(self, image: np.ndarray, box: Dict, 
                           ratio: float = 1.0) -> Dict:
        """
        Process single bounding box - Android getResultForSingleBox equivalent
        """
        height, width = image.shape[:2]
        
        # Apply ratio scaling
        left = int((box['left'] * ratio) + 1)
        right = int(box['right'] * ratio)
        top = int((box['top'] * ratio) + 1)
        bottom = int(box['bottom'] * ratio)
        
        # Ensure bounds are within image
        left = max(0, min(left, width - 1))
        right = max(0, min(right, width))
        top = max(0, min(top, height - 1))
        bottom = max(0, min(bottom, height))
        
        # Initialize counters
        c1_counter = 0
        c2_counter = 0
        c1_pitch_count = 0
        c2_pitch_count = 0
        is_c1 = False
        is_c2 = False
        area_count = 0
        
        pixels_list = []  # List of (type, count) tuples
        
        # Scan pixels row by row (like Android nested loops)
        for x in range(left, right + 1):
            for y in range(top, bottom + 1):
                if y >= height or x >= width:
                    break
                
                try:
                    # Get BGR pixel (OpenCV uses BGR)
                    b, g, r = image[y, x]
                    
                    # Check if pixel matches C1 range
                    if (box['c1_r_from'] <= r <= box['c1_r_to'] and
                        box['c1_g_from'] <= g <= box['c1_g_to'] and
                        box['c1_b_from'] <= b <= box['c1_b_to']):
                        
                        c1_counter += 1
                        is_c1 = True
                        c1_pitch_count += 1
                        
                        # If we were counting C2, save the pitch
                        if is_c2:
                            if c2_pitch_count > box['c2_pixel_count_range']:
                                pixels_list.append(('c2', c2_pitch_count))
                            c2_pitch_count = 0
                            is_c2 = False
                    
                    # Check if pixel matches C2 range
                    elif (box['c2_r_from'] <= r <= box['c2_r_to'] and
                          box['c2_g_from'] <= g <= box['c2_g_to'] and
                          box['c2_b_from'] <= b <= box['c2_b_to']):
                        
                        c2_counter += 1
                        is_c2 = True
                        c2_pitch_count += 1
                        
                        # If we were counting C1, save the pitch
                        if is_c1:
                            if c1_pitch_count > box['c1_pixel_count_range']:
                                pixels_list.append(('c1', c1_pitch_count))
                            c1_pitch_count = 0
                            is_c1 = False
                    
                    area_count += 1
                    
                except Exception as e:
                    continue
        
        # Process pitch lists
        c1_pitch_list = [count for type_, count in pixels_list if type_ == 'c1']
        c2_pitch_list = [count for type_, count in pixels_list if type_ == 'c2']
        
        # Calculate total pixels in box
        total_pixels = (right - left) * (bottom - top)
        
        # Calculate percentages
        c1_percentage = (c1_counter / total_pixels * 100) if total_pixels > 0 else 0
        c2_percentage = (c2_counter / total_pixels * 100) if total_pixels > 0 else 0
        
        # Determine verdict based on pixel_range threshold
        verdict = self._calculate_verdict(
            c1_percentage, c2_percentage,
            box.get('pixel_range', 50.0),
            box.get('greater_less_than', 'GREATER_THAN'),
            box.get('ok_nok', 'OK')
        )
        
        return {
            'box_id': f"{box['model_id']}_{box['position']}",
            'position': box['position'],
            'c1_pixel_count': c1_counter,
            'c1_percentage': round(c1_percentage, 2),
            'c1_min_pitch': min(c1_pitch_list) if c1_pitch_list else 0,
            'c1_max_pitch': max(c1_pitch_list) if c1_pitch_list else 0,
            'c1_pitch_list': c1_pitch_list,
            'c2_pixel_count': c2_counter,
            'c2_percentage': round(c2_percentage, 2),
            'c2_min_pitch': min(c2_pitch_list) if c2_pitch_list else 0,
            'c2_max_pitch': max(c2_pitch_list) if c2_pitch_list else 0,
            'c2_pitch_list': c2_pitch_list,
            'area_count': area_count,
            'total_pixels': total_pixels,
            'verdict': verdict,
            'box_coords': {
                'left': left, 'right': right,
                'top': top, 'bottom': bottom
            }
        }
    
    def _calculate_verdict(self, c1_pct: float, c2_pct: float,
                          threshold: float, comparison: str, 
                          ok_result: str) -> str:
        """
        Calculate OK/NOK verdict based on percentages and threshold
        """
        # Use C1 percentage for comparison
        value = c1_pct
        
        if comparison == 'GREATER_THAN':
            matches = value >= threshold
        else:  # LESS_THAN
            matches = value <= threshold
        
        if matches:
            return ok_result
        else:
            return 'NOK' if ok_result == 'OK' else 'OK'
    
    # ==================== RING DETECTION ====================
    
    def detect_colors_in_rings(self, image: np.ndarray, 
                               rings: List[Dict]) -> List[Dict]:
        """
        Detect colors in ring portions - Android getResultsForRing equivalent
        
        Ring format:
        {
            'id': 1,
            'model_id': 'CD',
            'position': 1,
            'center_x': 640,
            'center_y': 360,
            'inner_radius': 100,
            'outer_radius': 200,
            'portion_count': 8,
            'r_from': 0, 'g_from': 0, 'b_from': 0,
            'r_to': 50, 'g_to': 50, 'b_to': 50,
            'model_set_point_from': 10,
            'model_set_point_to': 100
        }
        """
        results = []
        
        for ring in rings:
            result = self._process_single_ring(image, ring)
            results.append(result)
        
        return results
    
    def _process_single_ring(self, image: np.ndarray, ring: Dict) -> Dict:
        """
        Process single ring - Android countPixelsInRingPortions equivalent
        """
        height, width = image.shape[:2]
        
        center_x = ring['center_x']
        center_y = ring['center_y']
        inner_radius = ring['inner_radius']
        outer_radius = ring['outer_radius']
        portion_count = ring['portion_count']
        
        # Initialize portion counters
        portion_pixels = [0] * portion_count
        
        # Scan all pixels in the ring area
        for x in range(width):
            for y in range(height):
                # Calculate distance from center
                distance = math.sqrt((x - center_x)**2 + (y - center_y)**2)
                
                # Check if pixel is within ring
                if inner_radius <= distance <= outer_radius:
                    # Calculate angle (in degrees)
                    angle = math.degrees(math.atan2(y - center_y, x - center_x))
                    normalized_angle = (angle + 360) % 360
                    
                    # Determine portion index
                    portion_index = int((normalized_angle / 360) * portion_count)
                    
                    # Get pixel color
                    b, g, r = image[y, x]
                    
                    # Check if pixel matches RGB range
                    if (ring['r_from'] <= r <= ring['r_to'] and
                        ring['g_from'] <= g <= ring['g_to'] and
                        ring['b_from'] <= b <= ring['b_to']):
                        
                        portion_pixels[portion_index] += 1
        
        # Calculate statistics
        total_pixels = sum(portion_pixels)
        avg_pixels = sum(portion_pixels) / portion_count if portion_count > 0 else 0
        min_pixels = min(portion_pixels) if portion_pixels else 0
        max_pixels = max(portion_pixels) if portion_pixels else 0
        
        # Determine verdict based on set points
        verdict = self._calculate_ring_verdict(
            total_pixels, 
            ring.get('model_set_point_from', 0),
            ring.get('model_set_point_to', 999999)
        )
        
        return {
            'ring_id': f"{ring['model_id']}_{ring['position']}",
            'position': ring['position'],
            'total_pixels': total_pixels,
            'average_pixels': round(avg_pixels, 2),
            'min_pixels': min_pixels,
            'max_pixels': max_pixels,
            'portion_pixels': portion_pixels,
            'portion_count': portion_count,
            'verdict': verdict,
            'ring_coords': {
                'center_x': center_x,
                'center_y': center_y,
                'inner_radius': inner_radius,
                'outer_radius': outer_radius
            }
        }
    
    def _calculate_ring_verdict(self, total_pixels: int, 
                                min_threshold: int, max_threshold: int) -> str:
        """
        Calculate verdict for ring based on pixel count thresholds
        """
        if min_threshold <= total_pixels <= max_threshold:
            return 'OK'
        else:
            return 'NOK'
    
    # ==================== GENERAL ROI COLOR DETECTION ====================
    
    def detect_colors_in_roi(self, image: np.ndarray, roi: Dict,
                            color_ranges: List[Dict]) -> Dict:
        """
        General purpose color detection in ROI
        
        ROI format:
        {
            'type': 'rectangle' | 'circle' | 'polygon',
            'coords': [...] # normalized 0-1
        }
        
        Color ranges format:
        [{
            'name': 'red',
            'r_from': 200, 'r_to': 255,
            'g_from': 0, 'g_to': 50,
            'b_from': 0, 'b_to': 50
        }]
        """
        height, width = image.shape[:2]
        
        # Extract ROI mask
        mask = self._create_roi_mask(image, roi)

        # Vectorized counting for better performance
        results = []
        total_roi_pixels = int(np.count_nonzero(mask))

        # Split channels for vectorized comparison
        b_chan = image[:, :, 0]
        g_chan = image[:, :, 1]
        r_chan = image[:, :, 2]

        for color_range in color_ranges:
            # Create boolean mask where pixels match color ranges
            cond_r = (r_chan >= color_range['r_from']) & (r_chan <= color_range['r_to'])
            cond_g = (g_chan >= color_range['g_from']) & (g_chan <= color_range['g_to'])
            cond_b = (b_chan >= color_range['b_from']) & (b_chan <= color_range['b_to'])

            match_mask = cond_r & cond_g & cond_b & (mask > 0)

            count = int(np.count_nonzero(match_mask))
            percentage = (count / total_roi_pixels * 100) if total_roi_pixels > 0 else 0

            # Collect a sample of matched pixels (up to 100) for debugging/UI
            ys, xs = np.nonzero(match_mask)
            matched_pixels = []
            sample_count = min(100, len(xs))
            for i in range(sample_count):
                x = int(xs[i]); y = int(ys[i])
                matched_pixels.append({'x': x, 'y': y, 'r': int(r_chan[y, x]), 'g': int(g_chan[y, x]), 'b': int(b_chan[y, x])})

            results.append({
                'color_name': color_range.get('name', 'unknown'),
                'pixel_count': count,
                'percentage': round(float(percentage), 2),
                'matched_pixels': matched_pixels,
                'total_matched': int(len(xs))
            })
        
        return {
            'roi_type': roi['type'],
            'total_roi_pixels': total_roi_pixels,
            'color_results': results,
            'summary': self._create_color_summary(results)
        }
    
    def _create_roi_mask(self, image: np.ndarray, roi: Dict) -> np.ndarray:
        """
        Create binary mask for ROI
        """
        height, width = image.shape[:2]
        mask = np.zeros((height, width), dtype=np.uint8)
        
        roi_type = roi.get('type', 'rectangle')
        coords = roi.get('coords', [])
        # support additional types: 'line' and 'freehand'
        
        if roi_type == 'rectangle' and len(coords) >= 4:
            # Rectangle: [x, y, w, h] normalized
            x = int(coords[0] * width)
            y = int(coords[1] * height)
            w = int(coords[2] * width)
            h = int(coords[3] * height)
            mask[y:y+h, x:x+w] = 255
        
        elif roi_type == 'circle' and len(coords) >= 3:
            # Circle: [cx, cy, radius] normalized
            cx = int(coords[0] * width)
            cy = int(coords[1] * height)
            radius = int(coords[2] * min(width, height))
            cv2.circle(mask, (cx, cy), radius, 255, -1)
        
        elif roi_type == 'polygon' and len(coords) >= 6:
            # Polygon: [[x1,y1], [x2,y2], ...] normalized
            points = []
            for i in range(0, len(coords), 2):
                px = int(coords[i] * width)
                py = int(coords[i+1] * height)
                points.append([px, py])
            points = np.array([points], dtype=np.int32)
            cv2.fillPoly(mask, points, 255)
        
        elif roi_type == 'line' and len(coords) >= 4:
            # Line: [x1,y1,x2,y2] normalized (draw a thick line as mask)
            x1 = int(coords[0] * width)
            y1 = int(coords[1] * height)
            x2 = int(coords[2] * width)
            y2 = int(coords[3] * height)
            # thickness proportional to image size or provided as 5th coord
            if len(coords) >= 5:
                thickness = int(coords[4] * min(width, height))
            else:
                thickness = max(1, int(0.01 * min(width, height)))
            cv2.line(mask, (x1, y1), (x2, y2), 255, thickness)

        elif roi_type == 'freehand' and len(coords) >= 4:
            # Freehand: flat list of points [x1,y1,x2,y2,...]
            points = []
            for i in range(0, len(coords) - 1, 2):
                px = int(coords[i] * width)
                py = int(coords[i+1] * height)
                points.append((px, py))
            # Draw lines between consecutive points with thickness
            thickness = max(1, int(0.01 * min(width, height)))
            for i in range(len(points) - 1):
                cv2.line(mask, points[i], points[i+1], 255, thickness)
        
        return mask
    
    def _create_color_summary(self, results: List[Dict]) -> Dict:
        """
        Create summary of color detection results
        """
        dominant = max(results, key=lambda x: x['percentage']) if results else None
        
        return {
            'dominant_color': dominant['color_name'] if dominant else None,
            'dominant_percentage': dominant['percentage'] if dominant else 0,
            'total_colors_detected': len([r for r in results if r['percentage'] > 1.0]),
            'all_colors': [
                {
                    'name': r['color_name'],
                    'percentage': r['percentage']
                }
                for r in sorted(results, key=lambda x: x['percentage'], reverse=True)
            ]
        }
    
    # ==================== VISUALIZATION ====================
    
    def draw_results_on_image(self, image: np.ndarray, 
                             boxes: List[Dict] = None,
                             rings: List[Dict] = None,
                             results: List[Dict] = None) -> np.ndarray:
        """
        Draw detection results on image for visualization
        """
        output = image.copy()
        
        # Draw boxes
        if boxes:
            for i, box in enumerate(boxes):
                left = box['left']
                right = box['right']
                top = box['top']
                bottom = box['bottom']
                
                # Draw rectangle
                color = (0, 255, 0) if results and results[i].get('verdict') == 'OK' else (0, 0, 255)
                cv2.rectangle(output, (left, top), (right, bottom), color, 2)
                
                # Draw label
                label = f"Box {box['position']}"
                if results and i < len(results):
                    label += f" ({results[i]['verdict']})"
                cv2.putText(output, label, (left, top - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        # Draw rings
        if rings:
            for i, ring in enumerate(rings):
                cx = int(ring['center_x'])
                cy = int(ring['center_y'])
                inner_r = int(ring['inner_radius'])
                outer_r = int(ring['outer_radius'])
                
                # Draw circles
                color = (0, 255, 0) if results and results[i].get('verdict') == 'OK' else (0, 0, 255)
                cv2.circle(output, (cx, cy), inner_r, color, 2)
                cv2.circle(output, (cx, cy), outer_r, color, 2)
                
                # Draw portions
                portion_count = ring['portion_count']
                for j in range(portion_count):
                    angle = (j * 360 / portion_count) * np.pi / 180
                    x1 = int(cx + inner_r * np.cos(angle))
                    y1 = int(cy + inner_r * np.sin(angle))
                    x2 = int(cx + outer_r * np.cos(angle))
                    y2 = int(cy + outer_r * np.sin(angle))
                    cv2.line(output, (x1, y1), (x2, y2), color, 1)
        
        return output


# ==================== USAGE EXAMPLE ====================

def example_usage():
    """
    Example showing how to use the ColorDetectionEngine
    """
    engine = ColorDetectionEngine()
    
    # Load image
    image = cv2.imread('test_image.jpg')
    if image is None:
        print("Could not load image")
        return
    
    # Example 1: Bounding Box Detection
    boxes = [
        {
            'id': 1,
            'model_id': 'CD',
            'position': 1,
            'left': 100,
            'right': 200,
            'top': 50,
            'bottom': 150,
            'c1_r_from': 0, 'c1_g_from': 0, 'c1_b_from': 0,
            'c1_r_to': 50, 'c1_g_to': 50, 'c1_b_to': 50,
            'c2_r_from': 200, 'c2_g_from': 200, 'c2_b_from': 200,
            'c2_r_to': 255, 'c2_g_to': 255, 'c2_b_to': 255,
            'c1_pixel_count_range': 10,
            'c2_pixel_count_range': 10,
            'pixel_range': 50.0,
            'greater_less_than': 'GREATER_THAN',
            'ok_nok': 'OK'
        }
    ]
    
    box_results = engine.detect_colors_in_boxes(image, boxes)
    print("\nBounding Box Results:")
    print(json.dumps(box_results, indent=2))
    
    # Example 2: Ring Detection
    rings = [
        {
            'id': 1,
            'model_id': 'CD',
            'position': 1,
            'center_x': 320,
            'center_y': 240,
            'inner_radius': 50,
            'outer_radius': 100,
            'portion_count': 8,
            'r_from': 200, 'g_from': 0, 'b_from': 0,
            'r_to': 255, 'g_to': 50, 'b_to': 50,
            'model_set_point_from': 100,
            'model_set_point_to': 1000
        }
    ]
    
    ring_results = engine.detect_colors_in_rings(image, rings)
    print("\nRing Results:")
    print(json.dumps(ring_results, indent=2))
    
    # Visualize
    output_image = engine.draw_results_on_image(image, boxes, rings, 
                                                box_results + ring_results)
    cv2.imwrite('detection_results.jpg', output_image)


if __name__ == "__main__":
    example_usage()
package com.automationteknix.cd_poc_with_model.colordetection.ui

import android.content.Context
import android.graphics.*
import android.util.AttributeSet
import androidx.appcompat.widget.AppCompatImageView
import com.automationteknix.cd_poc_with_model.colordetection.database.box.BoundingBoxTableCD
import com.automationteknix.cd_poc_with_model.colordetection.data.Shape
import com.automationteknix.cd_poc_with_model.colordetection.database.ring.entity.Ring
import kotlin.math.cos
import kotlin.math.sin

class ShapesView(context: Context, attrs: AttributeSet) : AppCompatImageView(context, attrs) {


    private var shapes: ArrayList<Shape>? = null
    private var type: String = "Set"
    private var strokeColor = Color.GREEN
    private var textColor = Color.RED
    private val strokeWidth = 4f


    private val separationPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        style = Paint.Style.STROKE
        strokeWidth = this@ShapesView.strokeWidth
        color = strokeColor
    }

    private val shapePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        style = Paint.Style.STROKE
        strokeWidth = this@ShapesView.strokeWidth
        color = strokeColor
    }

    private val textPaint = Paint().apply {
        color = textColor
        textSize = 35f
        textAlign = Paint.Align.CENTER
    }

    private val portionPath = Path()

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
        drawShapes(canvas)

    }

    private fun drawShapes(canvas: Canvas) {
        shapes.let { shapes ->
            if (shapes != null) {
                for (i in 0 until shapes.size) {
                    if (shapes[i] is Ring) {
                        drawRingWithPortions(canvas, shapes[i] as Ring)
                    } else if (shapes[i] is BoundingBoxTableCD) {

                        if (i == 0 || i == (shapes.size - 1) || type == "set")
                            drawBox(canvas, shapes[i] as BoundingBoxTableCD)

                    }
                }
            }
        }

    }

    private fun drawRingWithPortions(canvas: Canvas, ring: Ring) {
        val centerX = ring.centerX
        val centerY = ring.centerY
        val innerRadius = ring.innerRadius
        val outerRadius = ring.outerRadius
        val portionCount = ring.portionCount

        //Draw the outer circle
        canvas.drawCircle(centerX, centerY, outerRadius - strokeWidth / 2, shapePaint)

        //Draw the inner circle
        canvas.drawCircle(centerX, centerY, innerRadius + strokeWidth / 2, shapePaint)

        canvas.drawText(
            ring.position.toString(),
            centerX,
            centerY + textPaint.textSize / 2,
            textPaint
        )


        // Draw the ring portions
        val anglePerPortion = 360f / portionCount
        var startAngle = 0f
        for (i in 0 until portionCount) {
            portionPath.reset()

            portionPath.arcTo(
                centerX - outerRadius + strokeWidth / 2,
                centerY - outerRadius + strokeWidth / 2,
                centerX + outerRadius - strokeWidth / 2,
                centerY + outerRadius - strokeWidth / 2,
                startAngle,
                anglePerPortion,
                false
            )

            portionPath.arcTo(
                centerX - innerRadius - strokeWidth / 2,
                centerY - innerRadius - strokeWidth / 2,
                centerX + innerRadius + strokeWidth / 2,
                centerY + innerRadius + strokeWidth / 2,
                startAngle + anglePerPortion,
                -anglePerPortion,
                false
            )
            if (portionCount != 1) {
                canvas.drawPath(portionPath, separationPaint)
            }

            val angle = (i * anglePerPortion) + (anglePerPortion / 2)
            val angleRadians = Math.toRadians(angle.toDouble())

            val portionMidX =
                centerX + ((innerRadius + outerRadius) / 2f) * cos(angleRadians).toFloat()
            val portionMidY =
                centerY + ((innerRadius + outerRadius) / 2f) * sin(angleRadians).toFloat()

            canvas.drawText(
                (i + 1).toString(),
                portionMidX,
                portionMidY + textPaint.textSize / 2,
                textPaint
            )


            startAngle += anglePerPortion
        }
    }

    fun setRingsToDraw(rings: ArrayList<Ring>) {
        this.shapes = rings as ArrayList<Shape>
        invalidate()
    }

    private fun drawBox(canvas: Canvas, box: BoundingBoxTableCD) {

        val top = box.top.toFloat()
        val bottom = box.bottom.toFloat()
        val left = box.left.toFloat()
        val right = box.right.toFloat()

        // Draw bounding box around detected objects
        val drawableRect = RectF(left, top, right, bottom)
        canvas.drawRect(drawableRect, shapePaint)

        // Create text to display alongside detected objects
        val drawableText =
            box.position

        // Draw rect behind display text
        /*textBackgroundPaint.getTextBounds(drawableText, 0, drawableText.length, bounds)
        val textWidth = bounds.width()
        val textHeight = bounds.height()
        canvas.drawRect(
            left,
            top,
            left + textWidth + BOUNDING_RECT_TEXT_PADDING,
            top + textHeight + BOUNDING_RECT_TEXT_PADDING,
            textBackgroundPaint
        )*/

        // Draw text for detected object
        canvas.drawText(drawableText.toString(), left - 10, top - 10, textPaint)

    }

    fun setBoxesToDraw(
        detectionResults: ArrayList<BoundingBoxTableCD>,
        type: String = "set"
    ) {
        shapes = detectionResults as ArrayList<Shape>
        this.type = type
        // PreviewView is in FILL_START mode. So we need to scale up the bounding box to match with
        // the size that the captured images will be displayed.
        invalidate()
    }

}




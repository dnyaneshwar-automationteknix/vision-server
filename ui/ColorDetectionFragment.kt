package com.automationteknix.cd_poc_with_model.colordetection.ui

import android.annotation.SuppressLint
import android.app.Dialog
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Color
import android.net.Uri
import android.os.Bundle
import android.text.TextUtils
import android.util.Log
import android.view.LayoutInflater
import android.view.MotionEvent
import android.view.Surface
import android.view.View
import android.view.ViewGroup
import android.widget.PopupMenu
import android.widget.SeekBar
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.camera.core.Camera
import androidx.camera.core.CameraInfo
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageCapture
import androidx.camera.core.ImageCaptureException
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.core.content.ContextCompat
import androidx.core.view.drawToBitmap
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.recyclerview.widget.LinearLayoutManager
import com.automationteknix.scda.colordetection.database.rgbRange.entity.RGBRangeTable
import com.automationteknix.cd_poc_with_model.ApplicationClass
import com.automationteknix.cd_poc_with_model.CameraActivity
import com.automationteknix.cd_poc_with_model.CameraActivityML.Companion.TAG
import com.automationteknix.cd_poc_with_model.colordetection.adapters.AdapterBoundingBox
import com.automationteknix.cd_poc_with_model.colordetection.adapters.AdapterCDResult
import com.automationteknix.cd_poc_with_model.colordetection.data.ColorDetectionResult
import com.automationteknix.cd_poc_with_model.colordetection.data.ColorResult
import com.automationteknix.cd_poc_with_model.colordetection.data.ModelsTbl
import com.automationteknix.cd_poc_with_model.colordetection.database.box.BoundingBoxTableCD
import com.automationteknix.cd_poc_with_model.colordetection.database.box.BoundingBoxViewModelCD
import com.automationteknix.cd_poc_with_model.colordetection.database.rgbRange.entity.RGBViewModel
import com.automationteknix.cd_poc_with_model.colordetection.database.ring.entity.Ring
import com.automationteknix.cd_poc_with_model.commondatabaseclasses.ViewModelFactory
import com.automationteknix.cd_poc_with_model.customdailogs.CustomProgressDialog
import com.automationteknix.cd_poc_with_model.databinding.DialogBboxCdPixelrangeBinding
import com.automationteknix.cd_poc_with_model.databinding.DialogResultBinding
import com.automationteknix.cd_poc_with_model.databinding.FragmentColorDetectionBinding
import com.automationteknix.cd_poc_with_model.utils.CommonMethods
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.File
import java.io.InputStream
import java.text.SimpleDateFormat
import java.util.Date

class ColorDetectionFragment : Fragment() {

    private lateinit var outputDirectory: File
    private lateinit var originalBitmap: Bitmap
    private val selectedModel = ModelsTbl(zoomRatio = 1F, partName = "ColorDetection")

    private var imageCapture: ImageCapture? = null
    private var camera: Camera? = null
    private var cameraInfo: CameraInfo? = null

    var selectedRingPosition = 0

    private lateinit var adapterBoxItem: AdapterBoundingBox

    private val boundingBoxViewModelCD: BoundingBoxViewModelCD by viewModels {
        ViewModelFactory((requireActivity().application as ApplicationClass).bBoxCDRepo)
    }
    private val rgbViewModel: RGBViewModel by viewModels {
        ViewModelFactory((requireActivity().application as ApplicationClass).rgbRepository)
    }

    lateinit var binding: FragmentColorDetectionBinding

    private val imageChooserLauncher =
        registerForActivityResult(ActivityResultContracts.GetContent()) { uri: Uri? ->
            uri?.let {
                // Handle the selected image URI (e.g., display in an ImageView)
                binding.imagePreview.visibility = View.VISIBLE
                binding.cameraPreview.visibility = View.INVISIBLE
                binding.seekBar.visibility = View.INVISIBLE
                binding.tvPercent.visibility = View.INVISIBLE
                binding.btnCamera.visibility = View.INVISIBLE
                binding.btnProcess.visibility = View.VISIBLE
                binding.btnReCamera.visibility = View.VISIBLE
                binding.imagePreview.setImageURI(uri)
            }
        }

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View? {
        binding = FragmentColorDetectionBinding.inflate(layoutInflater)
        outputDirectory = requireActivity().filesDir
        setUpCamera()
        //initObserver()
        initRecyclerView()
        setupListeners()
        initBoxObserver()

        return binding.root
    }

    private fun initRecyclerView() {
        //ringsDialog.setContentView(ringsDialogBinding.root)

        binding.rvRings.layoutManager =
            LinearLayoutManager(
                requireActivity(),
                LinearLayoutManager.VERTICAL,
                false
            )


        //ringsDialog.show()
    }

    private fun initCameraListener(model: ModelsTbl?) {
        if (model == null) return
        binding.seekBar.progress = (model.zoomRatio * 10).toInt()
        binding.tvPercent.text = "${(model.zoomRatio * 10).toInt()}"
        seekBarChangedListeners(model)
        Log.e("Ring.Zoom", "${model.zoomRatio}")

    }

    private fun seekBarChangedListeners(modelsTbl: ModelsTbl?) {
        if (modelsTbl != null)
            binding.seekBar.setOnSeekBarChangeListener(object : SeekBar.OnSeekBarChangeListener {
                override fun onProgressChanged(p0: SeekBar?, p1: Int, p2: Boolean) {
                    modelsTbl.zoomRatio = p1.toFloat() / 10
                    Log.e("zoom ratio", "${modelsTbl.zoomRatio}")
                    updateZoom(modelsTbl.zoomRatio)

                }

                override fun onStartTrackingTouch(p0: SeekBar?) {

                }

                override fun onStopTrackingTouch(p0: SeekBar?) {

                }

            })
    }

    private fun updateZoom(zoomRatio: Float) {
        Log.e("tag", "ZOOM RATIO: $zoomRatio")
        binding.tvPercent.text = "${(zoomRatio * 10).toInt()}"
        Log.e("zoom ratio", "$zoomRatio")
        val maxZoom: Float = camera?.cameraInfo?.zoomState?.value?.maxZoomRatio ?: 0f
        if (zoomRatio > maxZoom)
            camera?.cameraControl?.setZoomRatio(maxZoom)
        else
            camera?.cameraControl?.setZoomRatio(zoomRatio)

    }

    override fun onResume() {
        super.onResume()
        //startCamera(selectedModel)
    }

    private fun setUpCamera() {
        startCamera(selectedModel)
        initCameraListener(selectedModel)
    }

    private fun startCamera(model: ModelsTbl) {

       // binding.btnProcess.visibility = View.INVISIBLE
        binding.cameraPreview.visibility = View.VISIBLE
        binding.seekBar.visibility = View.VISIBLE
        binding.tvPercent.visibility = View.VISIBLE


        val cameraProviderFeature = ProcessCameraProvider.getInstance(requireActivity())
        cameraProviderFeature.addListener(
            Runnable {
                val cameraProvider = cameraProviderFeature.get()
                val preview = Preview.Builder().build()
                preview.setSurfaceProvider(binding.cameraPreview.surfaceProvider)
                imageCapture = ImageCapture.Builder().build()

                val cameraSelector = CameraSelector.DEFAULT_BACK_CAMERA

                try {
                    cameraProvider.unbindAll()

                    camera =
                        cameraProvider.bindToLifecycle(
                            requireActivity(),
                            cameraSelector,
                            preview,
                            imageCapture
                        )

                    // TODO: i faced problem that image is capturing extra area which is not visible
                    // TODO: in camera preview and requireActivity() is solved by setting viewport
                    val viewPort = binding.cameraPreview.viewPort
                    if (viewPort != null) {
                        imageCapture?.setCropAspectRatio(viewPort.aspectRatio)

                    }

                    camera?.cameraControl?.enableTorch(false)
                    cameraInfo = camera?.cameraInfo

                    updateZoom(model.zoomRatio)
                    /*val sharedPreferences = getSharedPreferences(
                        CommonMethods.COMMON_SHARED_PREFERANCE,
                        MODE_PRIVATE
                    )*/
                    /*val delta = sharedPreferences.getFloat(CommonMethods.CAMERA_ZOOM_RATIO, 0f)
                    Log.e("zoom ratio", "$delta")
                    camera?.cameraControl?.setZoomRatio(delta)*/
                } catch (_: Exception) {

                }
            },
            ContextCompat.getMainExecutor(requireActivity())
        )


    }

    private fun setupListeners() {
        binding.btnReCamera.setOnClickListener {
            binding.cameraPreview.visibility = View.VISIBLE
            binding.seekBar.visibility = View.VISIBLE
            binding.tvPercent.visibility = View.VISIBLE
            binding.btnCamera.visibility = View.VISIBLE
            binding.btnReCamera.visibility = View.INVISIBLE
            binding.imagePreview.visibility = View.INVISIBLE
            binding.btnProcess.visibility = View.INVISIBLE

        }

        binding.btnCamera.setOnLongClickListener {
            imageChooserLauncher.launch("image/*")
            true
        }

        binding.btnCamera.setOnClickListener {
            Thread.sleep(300)
            //(application as ApplicationClass).ringsSubmission()
            takePhoto()
            binding.btnCamera.visibility = View.INVISIBLE
        }

        binding.root.setOnClickListener { }
    }
    private fun toGrayscale(bitmap: Bitmap): Bitmap {
        val width = bitmap.width
        val height = bitmap.height
        val grayscaleBitmap = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888)

        for (i in 0 until width) {
            for (j in 0 until height) {
                val pixel = bitmap.getPixel(i, j)
                val gray =
                    (Color.red(pixel) * 0.3 + Color.green(pixel) * 0.59 + Color.blue(pixel) * 0.11).toInt()
                grayscaleBitmap.setPixel(i, j, Color.rgb(gray, gray, gray))
            }
        }
        return grayscaleBitmap
    }

    private fun takePhoto() {

        binding.imagePreview.visibility = View.VISIBLE
        binding.imagePreview.setImageBitmap(binding.cameraPreview.bitmap)
        binding.cameraPreview.visibility = View.INVISIBLE
        binding.seekBar.visibility = View.INVISIBLE
        binding.tvPercent.visibility = View.INVISIBLE
        binding.btnCamera.visibility = View.INVISIBLE
        binding.btnProcess.visibility = View.VISIBLE
        binding.btnReCamera.visibility = View.VISIBLE

        Log.e("tag", "before image capture")
        val imageCapture = imageCapture ?: return
        Log.e("tag", "after image capture")
        Log.e("tag", "rotation degree ${CameraActivity.rotationDegree}")
        when (CameraActivity.rotationDegree) {
            0 -> imageCapture.targetRotation = Surface.ROTATION_0
            90 -> imageCapture.targetRotation = Surface.ROTATION_90
            180 -> imageCapture.targetRotation = Surface.ROTATION_180
            270 -> imageCapture.targetRotation = Surface.ROTATION_270
        }

        val photoFile = createTempFile()
        val outputOptions = ImageCapture.OutputFileOptions.Builder(photoFile).build()
        //imageCapture.targetRotation=Surface.
        imageCapture.takePicture(
            outputOptions,
            ContextCompat.getMainExecutor(requireActivity()),
            object : ImageCapture.OnImageSavedCallback {
                override fun onError(exception: ImageCaptureException) {
                    Log.e("tag", exception.toString())
                }

                override fun onImageSaved(outputFileResults: ImageCapture.OutputFileResults) {
                    val savedUri = Uri.fromFile(photoFile)
                    val msg = "Photo capture succeeded: $savedUri"
                    Log.e("capture time", SimpleDateFormat("dd/MM/yyy hh:mm:ss:SSS").format(Date()))

                    val inputStream: InputStream? =
                        requireActivity().contentResolver.openInputStream(savedUri)
                    originalBitmap = BitmapFactory.decodeStream(inputStream)

                    //Toast.makeText(requireActivity(), msg, Toast.LENGTH_SHORT).show()
                    Log.d(TAG, msg)
                }
            })
        Log.e("output directory", outputDirectory.absolutePath)


    }


    private fun initBoxObserver() {
        boundingBoxViewModelCD.getBoundingBoxesWithModel(selectedModel.partName)
        boundingBoxViewModelCD.boundingBoxesWithModel.observe(viewLifecycleOwner) { boxes ->
            binding.ringimgevie.setBoxesToDraw(boxes)
            initBoxesAdapter(boxes)
            setUpSeekBarsForBoxes(boxes)
            setUpAddBtnForBoxes(boxes)
            setUpProcessBtn(boxes)
            setUpOnBoundingBoxMovement(boxes)
        }
    }

    private fun initBoxesAdapter(boxes: ArrayList<BoundingBoxTableCD>) {
        adapterBoxItem = AdapterBoundingBox(requireActivity(), boxes)

        adapterBoxItem.boxListeners = object : AdapterBoundingBox.BoxListeners {
            override fun onBoxClick(position: Int) {
                selectedRingPosition = position
            }

            override fun onEditClick(
                position: Int,
                box: BoundingBoxTableCD,
                adapter: AdapterBoundingBox
            ) {
                selectedRingPosition = position
                editBox(box, adapter, boxes)
            }

            override fun onDeleteClick(
                position: Int,
                box: BoundingBoxTableCD,
                adapter: AdapterBoundingBox
            ) {
                selectedRingPosition = position
                deleteBox(box, boxes, adapter)
            }

        }

        binding.rvRings.adapter = adapterBoxItem


    }


    private fun editBox(
        box: BoundingBoxTableCD,
        adapterBoundingBox: AdapterBoundingBox,
        boxes: ArrayList<BoundingBoxTableCD>
    ) {
        val dialogBinding =
            DialogBboxCdPixelrangeBinding.inflate(LayoutInflater.from(requireActivity()))
        val dialog = Dialog(requireActivity())
        dialog.setContentView(dialogBinding.root)
        dialogBinding.etHeight.setText("${box.bottom - box.top}")
        dialogBinding.etWidth.setText("${box.right - box.left}")
        dialogBinding.etPixelRange.setText("${box.pixel_range}")
        dialogBinding.etLessGreaterThan.setText(box.greater_less_than)
        dialogBinding.etOkNok.setText(box.ok_nok)
        dialogBinding.c1EtRgbFrom.setText("${box.c1_r_from},${box.c1_g_from},${box.c1_b_from}")
        dialogBinding.c1EtRgbTo.setText("${box.c1_r_to},${box.c1_g_to},${box.c1_b_to}")
        dialogBinding.c2EtRgbFrom.setText("${box.c2_r_from},${box.c2_g_from},${box.c2_b_from}")
        dialogBinding.c2EtRgbTo.setText("${box.c2_r_to},${box.c2_g_to},${box.c2_b_to}")
        dialogBinding.c1EtIgnorePixel.setText("${box.c1PixelCountRange}")
        dialogBinding.c2EtIgnorePixel.setText("${box.c2PixelCountRange}")
        dialogBinding.etLessGreaterThan.setOnClickListener { v ->
            val popupMenu = PopupMenu(requireActivity(), v)
            popupMenu.menu.add(Ring.GREATER_THAN)
            popupMenu.menu.add(Ring.LESS_THAN)
            popupMenu.setOnMenuItemClickListener {
                if (it.title.toString().equals(Ring.LESS_THAN)) {
                    dialogBinding.etLessGreaterThan.setText(Ring.LESS_THAN)

                } else if (it.title.toString().equals(Ring.GREATER_THAN)) {
                    dialogBinding.etLessGreaterThan.setText(Ring.GREATER_THAN)
                }

                false
            }

            popupMenu.show()
        }
        dialogBinding.etOkNok.setOnClickListener { v ->
            val popupMenu = PopupMenu(requireActivity(), v)
            popupMenu.menu.add(ColorDetectionResult.RESULT_OK)
            popupMenu.menu.add(ColorDetectionResult.RESULT_NOK)
            popupMenu.setOnMenuItemClickListener {
                if (it.title.toString().equals(ColorDetectionResult.RESULT_OK)) {
                    dialogBinding.etOkNok.setText(ColorDetectionResult.RESULT_OK)
                } else if (it.title.toString().equals(ColorDetectionResult.RESULT_NOK)) {
                    dialogBinding.etOkNok.setText(ColorDetectionResult.RESULT_NOK)
                }

                false
            }

            popupMenu.show()
        }
        dialogBinding.btnSubmit.setOnClickListener {
            val heightString = dialogBinding.etHeight.text.toString()
            val widthString = dialogBinding.etWidth.text.toString()
            val strPixelRange = dialogBinding.etPixelRange.text.toString()
            val strC1RangeFrom = dialogBinding.c1EtRgbFrom.text.toString()
            val strC1RangeTo = dialogBinding.c1EtRgbTo.text.toString()
            val strC2RangeFrom = dialogBinding.c2EtRgbFrom.text.toString()
            val strC2RangeTo = dialogBinding.c2EtRgbTo.text.toString()
            val c1IgnorePixel = dialogBinding.c1EtIgnorePixel.text.toString()
            val c2IgnorePixel = dialogBinding.c2EtIgnorePixel.text.toString()

            if (TextUtils.isEmpty(heightString)) {
                Toast.makeText(requireContext(), "Please Enter Height", Toast.LENGTH_SHORT)
                    .show()
                return@setOnClickListener
            }

            if (TextUtils.isEmpty(widthString)) {
                Toast.makeText(requireContext(), "Please Enter Width", Toast.LENGTH_SHORT)
                    .show()
                return@setOnClickListener
            }

            if (TextUtils.isEmpty(strPixelRange)) {
                Toast.makeText(
                    requireContext(),
                    "Please Enter Pixel Range",
                    Toast.LENGTH_SHORT
                )
                    .show()
                return@setOnClickListener
            }
            if (TextUtils.isEmpty(strC1RangeFrom)) {
                Toast.makeText(requireContext(), "Please Enter Range", Toast.LENGTH_SHORT)
                    .show()
                return@setOnClickListener;
            }

            if (TextUtils.isEmpty(strC1RangeTo)) {
                Toast.makeText(requireContext(), "Please Enter Range", Toast.LENGTH_SHORT)
                    .show()
                return@setOnClickListener;
            }

            if (TextUtils.isEmpty(strC2RangeFrom)) {
                Toast.makeText(requireContext(), "Please Enter Range", Toast.LENGTH_SHORT)
                    .show()
                return@setOnClickListener;
            }

            if (TextUtils.isEmpty(strC2RangeTo)) {
                Toast.makeText(requireContext(), "Please Enter Range", Toast.LENGTH_SHORT)
                    .show()
                return@setOnClickListener;
            }
            if (TextUtils.isEmpty(c1IgnorePixel)) {
                Toast.makeText(
                    requireContext(),
                    "Please Enter C1 Ignore Pixels",
                    Toast.LENGTH_SHORT
                ).show()
                return@setOnClickListener;
            }
            if (TextUtils.isEmpty(c2IgnorePixel)) {

                CommonMethods.mt(
                    requireActivity(),
                    "Please Enter C2 Ignore Pixels"
                )

                return@setOnClickListener;
            }
            val arrC1RangeFrom = strC1RangeFrom.split(",");
            val arrC1RangeTo = strC1RangeTo.split(",")

            val arrC2RangeFrom = strC2RangeFrom.split(",");
            val arrC2RangeTo = strC2RangeTo.split(",")

            if (arrC1RangeFrom.size < 3 || arrC1RangeTo.size < 3) {
                CommonMethods.mt(
                    requireActivity(),
                    "Please Enter Valid Range"
                )

                return@setOnClickListener
            }
            if (arrC2RangeFrom.size < 3 || arrC2RangeTo.size < 3) {
                Toast.makeText(
                    requireContext(),
                    "Please Enter Valid Range",
                    Toast.LENGTH_SHORT
                )
                    .show()
                return@setOnClickListener;
            }
            var c1rFrom = 0
            var c1gFrom = 0
            var c1bFrom = 0
            var c1rTo = 0
            var c1gTo = 0
            var c1bTo = 0

            var c2rFrom = 0
            var c2gFrom = 0
            var c2bFrom = 0
            var c2rTo = 0
            var c2gTo = 0
            var c2bTo = 0
            try {
                c1rFrom = arrC1RangeFrom[0].toInt()
                c1gFrom = arrC1RangeFrom[1].toInt()
                c1bFrom = arrC1RangeFrom[2].toInt()

                c1rTo = arrC1RangeTo[0].toInt()
                c1gTo = arrC1RangeTo[1].toInt()
                c1bTo = arrC1RangeTo[2].toInt()

                c2rFrom = arrC2RangeFrom[0].toInt()
                c2gFrom = arrC2RangeFrom[1].toInt()
                c2bFrom = arrC2RangeFrom[2].toInt()

                c2rTo = arrC2RangeTo[0].toInt()
                c2gTo = arrC2RangeTo[1].toInt()
                c2bTo = arrC2RangeTo[2].toInt()

            } catch (e: NumberFormatException) {
                Toast.makeText(
                    requireContext(),
                    "Please Enter Valid Range",
                    Toast.LENGTH_SHORT
                )
                    .show()
            }
            if (arrC1RangeFrom.size < 3 || arrC1RangeTo.size < 3) {
                Toast.makeText(
                    requireContext(),
                    "Please Enter Valid Range",
                    Toast.LENGTH_SHORT
                )
                    .show()
                return@setOnClickListener;
            }
            if (arrC2RangeFrom.size < 3 || arrC2RangeTo.size < 3) {
                Toast.makeText(
                    requireContext(),
                    "Please Enter Valid Range",
                    Toast.LENGTH_SHORT
                )
                    .show()
                return@setOnClickListener;
            }
            val height = heightString.toInt()
            val width = widthString.toInt()

            val boxCopy = BoundingBoxTableCD(
                box.id,
                box.modelId,
                box.position,
                box.left,
                box.left + width,
                box.top,
                box.top + height,
                c1rFrom,
                c1gFrom,
                c1bFrom,
                c1rTo,
                c1gTo,
                c1bTo,
                c2rFrom,
                c2gFrom,
                c2bFrom,
                c2rTo,
                c2gTo,
                c2bTo,
                c1IgnorePixel.toInt(),
                c2IgnorePixel.toInt(),
                strPixelRange.toDouble(),
                dialogBinding.etLessGreaterThan.text.toString(),
                dialogBinding.etOkNok.text.toString(),
                false

            )

            saveBoundingBoxData(boxCopy)
            dialog.dismiss()

        }

        dialog.show()

    }

    private fun deleteBox(
        box: BoundingBoxTableCD,
        boxes: ArrayList<BoundingBoxTableCD>,
        adapterBoundingBox: AdapterBoundingBox
    ) {
        //boxes.removeAt(selectedRingPosition)
        deleteBoundingBox(box)
    }

    @SuppressLint("ClickableViewAccessibility")
    private fun setUpOnBoundingBoxMovement(boxes: ArrayList<BoundingBoxTableCD>) {

        binding.ringimgevie.setOnTouchListener { _, motionEvent ->

            if (boxes.size != 0) {
                binding.ringimgevie.post {
                    val bitmap = binding.ringimgevie

                    when (motionEvent.action) {
                        MotionEvent.ACTION_DOWN -> {
                            attachTouchPositions(motionEvent, bitmap, boxes)
                        }

                        MotionEvent.ACTION_MOVE -> {
                            attachTouchPositions(motionEvent, bitmap, boxes)
                            binding.ringimgevie.setBoxesToDraw(
                                boxes
                            )
                        }

                        MotionEvent.ACTION_UP -> {
                            attachTouchPositions(motionEvent, bitmap, boxes)
                            //updateViewAndBBoxDataOnTouch(bitmap, boxes)
                        }

                    }

                }
            }
            true
        }


    }

    private fun attachTouchPositions(
        motionEvent: MotionEvent,
        bitmap: ShapesView,
        boxes: ArrayList<BoundingBoxTableCD>
    ) {
        val height =
            boxes[selectedRingPosition].bottom - boxes[selectedRingPosition].top

        val width =
            boxes[selectedRingPosition].right - boxes[selectedRingPosition].left

        if (motionEvent.x < bitmap.width && motionEvent.y < bitmap.height) {
            boxes[selectedRingPosition].top = motionEvent.y.toInt()
            boxes[selectedRingPosition].left = motionEvent.x.toInt()
            boxes[selectedRingPosition].bottom = (motionEvent.y + height).toInt()
            boxes[selectedRingPosition].right = (motionEvent.x + width).toInt()
            // Log.e("l:", "$l, r:$r")
            val horizontalPercent = (motionEvent.x / bitmap.width) * 100
            val verticalPercent = (motionEvent.y / bitmap.height) * 100
            // TODO: when you change progress onProgressChangeListner gets called and
            // todo bounding box will change
            binding.bottomSeekBar.progress = horizontalPercent.toInt()
            binding.leftSeekBar.progress = verticalPercent.toInt()
        }
    }


    private fun updateViewAndBBoxDataOnTouch(
        boxes: ArrayList<BoundingBoxTableCD>
    ) {
        binding.ringimgevie.setBoxesToDraw(
            boxes,
        )

        boundingBoxViewModelCD.updateBoundingBox(
            boxes[selectedRingPosition]
        )

    }

    private fun setUpSeekBarsForBoxes(boxes: ArrayList<BoundingBoxTableCD>) {

        binding.bottomSeekBar.setOnSeekBarChangeListener(object : SeekBar.OnSeekBarChangeListener {
            override fun onProgressChanged(p0: SeekBar?, p1: Int, p2: Boolean) {
                binding.tvBSeekBarValue.text = "$p1%"
                if (boxes.size >= selectedRingPosition && boxes.size > 0) {
                    val bitmap = binding.ringimgevie
                    val width = boxes[selectedRingPosition].right - boxes[selectedRingPosition].left
                    val l = ((bitmap.width) / 100) * p1

                    val r = l + width

                    Log.e("l:", "$l, r:$r")
                    boxes[selectedRingPosition].left = l
                    boxes[selectedRingPosition].right = r

                    updateViewAndBBoxDataOnTouch(boxes)
                }
            }

            override fun onStartTrackingTouch(p0: SeekBar?) {
                Log.e("hi", "hello")
            }

            override fun onStopTrackingTouch(p0: SeekBar?) {
                Log.e("hi", "namaste")
            }

        })
        binding.leftSeekBar.setOnSeekBarChangeListener(object : SeekBar.OnSeekBarChangeListener {
            override fun onProgressChanged(p0: SeekBar?, p1: Int, p2: Boolean) {
                binding.tvLSeekBarValue.text = "$p1%"
                if (boxes.size > 0) {
                    val bitmap = binding.ringimgevie
                    val height =
                        boxes[selectedRingPosition].bottom - boxes[selectedRingPosition].top
                    val t = ((bitmap.height * p1) / 100)
                    val b = t + height

                    Log.e("t:", "$t, b:$b")
                    boxes[selectedRingPosition].top = t
                    boxes[selectedRingPosition].bottom = b

                    updateViewAndBBoxDataOnTouch(boxes)

                }
            }

            override fun onStartTrackingTouch(p0: SeekBar?) {
                Log.e("hi", "hello")
            }

            override fun onStopTrackingTouch(p0: SeekBar?) {
                Log.e("hi", "namaste")
            }

        })
    }

    private fun deleteBoundingBox(box: BoundingBoxTableCD) {
        //refresh overlayView when bounding box is deleted
        box.syncStatus = false
        boundingBoxViewModelCD.deleteBoundingBox(box.id)
        boundingBoxViewModelCD.syncStatusFalse()
        Thread.sleep(500)
        //(requireActivity().application as ApplicationClass).boundingBoxSubmission()
        boundingBoxViewModelCD.getBoundingBoxesWithModel(box.modelId)
        if (selectedRingPosition > 0) {
            selectedRingPosition -= 1
        }
    }

    private fun saveBoundingBoxData(box: BoundingBoxTableCD) {
        boundingBoxViewModelCD.updateBoundingBox(box)
        Thread.sleep(300)

        //(requireActivity().application as ApplicationClass).boundingBoxSubmission()

        boundingBoxViewModelCD.getBoundingBoxesWithModel(box.modelId)

    }

    private fun setUpAddBtnForBoxes(boxes: ArrayList<BoundingBoxTableCD>) {
        binding.btnAdd.setOnClickListener {

            CoroutineScope(Dispatchers.IO).launch {
                val box: BoundingBoxTableCD
                if (boxes.size > 0) {
                    box = boxes.last()
                    box.id = 0
                    box.position = (boxes.last().position + 1)
                } else {
                    box = BoundingBoxTableCD(
                        id = 0,
                        modelId = selectedModel.partName,
                        position = 1,
                        syncStatus = false
                    )
                }
                boundingBoxViewModelCD.insert(
                    box
                )

                withContext(Dispatchers.Main) {
                    boundingBoxViewModelCD.getBoundingBoxesWithModel(selectedModel.partName)
                }
            }

        }
    }


    private fun setUpProcessBtn(boxes: ArrayList<BoundingBoxTableCD>) {
        binding.btnProcess.setOnClickListener {
            var bitmap = binding.imagePreview.drawToBitmap()
            processBitmap(boxes, bitmap)

        }
    }

    private fun processBitmap(boxes: ArrayList<BoundingBoxTableCD>, bitmap: Bitmap) {

        val resultList = mutableListOf<ColorResult>()
        val rList = ArrayList<Int>()
        val gList = ArrayList<Int>()
        val bList = ArrayList<Int>()

        val dialog = CustomProgressDialog("Getting results", requireActivity())
        dialog.show()
        CoroutineScope(Dispatchers.IO).launch {
            val job = CoroutineScope(Dispatchers.IO).launch {
                if (boxes.size > 0) {
                    for (box in boxes) {

                        val left = box.left.toInt()
                        val right = box.right.toInt()
                        val top = box.top
                        val bottom = box.bottom
                        for (x in (left)..right) {
                            for (y in (top)..bottom) {
                                if (y > bitmap.height || x > bitmap.width)
                                    break
                                try {
                                    val color1 = bitmap.getColor(/*leftX, centerY*/x, y).toArgb()
                                    val r = Color.red(color1)
                                    val g = Color.green(color1)
                                    val b = Color.blue(color1)

                                    rList.add(r)
                                    gList.add(g)
                                    bList.add(b)
                                    resultList.add(
                                        ColorResult(
                                            box.position.toString(),
                                            x,
                                            y,
                                            r,
                                            g,
                                            b
                                        )
                                    )
                                } catch (_: IllegalArgumentException) {
                                }

                            }
                        }

                    }
                }
            }

            job.join()
            val maxColor = ColorResult(
                "Max",
                0,
                0,
                rList.toIntArray().maxOrNull() ?: 0,
                gList.toIntArray().maxOrNull() ?: 0,
                bList.toIntArray().maxOrNull() ?: 0
            )

            resultList.add(
                0,
                maxColor
            )
            val minColor = ColorResult(
                "Min",
                0,
                0,
                rList.toIntArray().minOrNull() ?: 0,
                gList.toIntArray().minOrNull() ?: 0,
                bList.toIntArray().minOrNull() ?: 0
            )
            resultList.add(
                1,
                minColor
            )

            dialog.dismiss()
            if (resultList.size > 0) {
                requireActivity().runOnUiThread {
                    val resultDialogBinding = DialogResultBinding.inflate(layoutInflater)
                    resultDialogBinding.rvResult.layoutManager =
                        LinearLayoutManager(requireActivity())
                    val adapterResult = AdapterCDResult(requireActivity(), resultList)
                    resultDialogBinding.rvResult.adapter = adapterResult

                    val resultDialog = Dialog(requireActivity())
                    resultDialog.setContentView(resultDialogBinding.root)
                    resultDialogBinding.btnSave.setOnClickListener {
                        val name = resultDialogBinding.edtName.text.toString()
                        if (name.isEmpty()) {
                            Toast.makeText(context, "Enter Name To Save", Toast.LENGTH_SHORT).show()
                        } else {
                            rgbViewModel.insert(
                                RGBRangeTable(
                                    0,
                                    name,
                                    minColor.r,
                                    minColor.g,
                                    minColor.b,
                                    maxColor.r,
                                    maxColor.g,
                                    maxColor.b,
                                    CommonMethods.INSERT
                                )
                            )
                            Toast.makeText(context, "Save  Successfully!", Toast.LENGTH_SHORT)
                                .show()
                            resultDialogBinding.edtName.setText("")

                            /*CoroutineScope(Dispatchers.IO).launch {
                                if(!MainActivity.isRGBSubmissionRunning) {
                                    rgbViewModel.updateRGBRange(
                                        MainActivity.getRGBSubmissionHandler(
                                            requireActivity()
                                        )
                                    )

                                    MainActivity.isRGBSubmissionRunning = true
                                }

                            }*/

                        }


                    }

                    resultDialogBinding.btnClose.setOnClickListener {
                        resultDialog.dismiss()
                    }
                    resultDialog.setCancelable(false)
                    resultDialog.show()
                    Log.e("resultSize", "${resultList.size}")
                    Log.e("resultList", resultList.toString())
                }
            }
        }
    }
}
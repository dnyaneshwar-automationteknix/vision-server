package com.automationteknix.cd_poc_with_model.colordetection.ui


import android.Manifest
import android.annotation.SuppressLint
import android.app.Activity
import android.app.Dialog
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Color
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.text.Html
import android.text.TextUtils
import android.util.Log
import android.view.LayoutInflater
import android.view.MotionEvent
import android.view.Surface
import android.view.View
import android.view.ViewGroup
import android.widget.AdapterView
import android.widget.ArrayAdapter
import android.widget.PopupMenu
import android.widget.SeekBar
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.annotation.RequiresApi
import androidx.appcompat.app.AlertDialog
import androidx.camera.core.Camera
import androidx.camera.core.CameraInfo
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageCapture
import androidx.camera.core.ImageCaptureException
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import androidx.core.view.drawToBitmap
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.recyclerview.widget.LinearLayoutManager
import com.automationteknix.cd_poc_with_model.ApplicationClass
import com.automationteknix.cd_poc_with_model.CameraActivity
import com.automationteknix.cd_poc_with_model.CameraActivityML.Companion.TAG
import com.automationteknix.cd_poc_with_model.FilterPaperPOCCameraActivity
import com.automationteknix.cd_poc_with_model.R
import com.automationteknix.cd_poc_with_model.colordetection.adapters.AdapterBoundingBox
import com.automationteknix.cd_poc_with_model.colordetection.adapters.AdapterIntResult
import com.automationteknix.cd_poc_with_model.colordetection.adapters.AdapterRingItem
import com.automationteknix.cd_poc_with_model.colordetection.data.ColorDetectionResult
import com.automationteknix.cd_poc_with_model.colordetection.database.box.BoundingBoxTableCD
import com.automationteknix.cd_poc_with_model.colordetection.database.box.BoundingBoxViewModelCD
import com.automationteknix.cd_poc_with_model.colordetection.database.ring.entity.Ring
import com.automationteknix.cd_poc_with_model.colordetection.database.ring.viewmodel.RingViewModel
import com.automationteknix.cd_poc_with_model.commondatabaseclasses.ViewModelFactory
import com.automationteknix.cd_poc_with_model.databinding.ActivitySetRingBinding
import com.automationteknix.cd_poc_with_model.databinding.DialogBboxCdPixelrangeBinding
import com.automationteknix.cd_poc_with_model.databinding.DialogResultBinding
import com.automationteknix.cd_poc_with_model.databinding.DialogRingSettingPixelrangeBinding
import com.automationteknix.cd_poc_with_model.databinding.RvModelItemBinding
import com.automationteknix.cd_poc_with_model.network.ServerData
import com.automationteknix.cd_poc_with_model.teamat.data.mstcommcs.MstCommCSViewModel
import com.automationteknix.cd_poc_with_model.utils.CommonMethods
import com.automationteknix.cd_poc_with_model.utils.CommonMethods.Companion.BOXES
import com.automationteknix.cd_poc_with_model.utils.CommonMethods.Companion.INSERT
import com.automationteknix.cd_poc_with_model.utils.CommonMethods.Companion.RINGS
import com.automationteknix.cd_poc_with_model.utils.CommonMethods.Companion.UPDATE
import com.automationteknix.cd_poc_with_model.utils.CommonMethods.Companion.mt
import com.automationteknix.cd_poc_with_model.wifimodule.WifiUtils
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.File
import java.io.InputStream
import java.text.SimpleDateFormat
import java.util.Date
import kotlin.math.atan2
import kotlin.math.pow
import kotlin.math.sqrt


class CDSettingsFragment : Fragment() {


    private lateinit var outputDirectory: File
    private lateinit var originalBitmap: Bitmap

    private var imageCapture: ImageCapture? = null
    private var camera: Camera? = null
    private var cameraInfo: CameraInfo? = null
    private var flashStatus = true
    private var zoomRatio: Float = 1F


    private val mstCommCSViewModel: MstCommCSViewModel by viewModels {
        ViewModelFactory((requireActivity().application as ApplicationClass).mstCommCSRepository)
    }
    private var serverImpl: WifiUtils.ServerImplementation? = null
    private var server: WifiUtils.Server? = null
    private var portNo = 0
    private var ipAddressCs = ""
    private val wifiUtils = WifiUtils()

    private var modelName: String = "CD"
    var selectedRingPosition = 0


    private val ringViewModel: RingViewModel by viewModels {
        ViewModelFactory((requireActivity().application as ApplicationClass).ringRepo)
    }

    private val boundingBoxViewModelCD: BoundingBoxViewModelCD by viewModels {
        ViewModelFactory((requireActivity().application as ApplicationClass).bBoxCDRepo)
    }


    private lateinit var adapterRingItem: AdapterRingItem
    private lateinit var adapterBoxItem: AdapterBoundingBox


    lateinit var binding: ActivitySetRingBinding
    private val commonMethods = CommonMethods()

    private var permissions = arrayOf(
        Manifest.permission.WRITE_EXTERNAL_STORAGE,
        Manifest.permission.READ_EXTERNAL_STORAGE,
        Manifest.permission.CAMERA,
        Manifest.permission.INTERNET,

        )

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
    ): View {
        // TODO: 04-01-2022 set Custom actionbar
        /*supportActionBar?.displayOptions = ActionBar.DISPLAY_SHOW_CUSTOM
        supportActionBar?.setCustomView(R.layout.actionbar_layout)*/
        binding = ActivitySetRingBinding.inflate(layoutInflater)
        //setContentView(binding.root)

        return binding.root
    }


    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        val shapeType = arguments?.getString("shapeType") ?: BOXES

        outputDirectory = getOutputDirectory()

        //zoomControlListeners()

        initSharedP()

        setUpCamera(zoomRatio)

        //initObserver()

        initRecyclerView()
        setupListeners()
        initModelSpinner(FilterPaperPOCCameraActivity.CD_MODELS)

        if (shapeType == RINGS) {
            initRingsObserver()
        } else if (shapeType == BOXES) {
            initBoxObserver()
        }

    }

    private fun initModelSpinner(operations: List<String>) {
        val operationsTitle = operations.map { it }.toCollection(ArrayList())
        operationsTitle.add(0, "Select operation")

        val operationAdapter = ArrayAdapter(
            requireContext(),
            android.R.layout.simple_spinner_item,
            operationsTitle
        )

        operationAdapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item)

        binding.operationSpinner.adapter = operationAdapter

        binding.operationSpinner.onItemSelectedListener =
            object : AdapterView.OnItemSelectedListener {

                override fun onItemSelected(
                    parent: AdapterView<*>?,
                    view: View?,
                    position: Int,
                    id: Long
                ) {
                    val selectedOperation = parent?.getItemAtPosition(position).toString()
                    modelName = selectedOperation
                    Log.e("selectedOperation", selectedOperation)
                    boundingBoxViewModelCD.getBoundingBoxesWithModel(modelName)
                }

                override fun onNothingSelected(p0: AdapterView<*>?) {}
            }
    }


    private fun setUpAddRingBtn(rings: ArrayList<Ring>) {
        binding.btnAdd.setOnClickListener {
            addRingsInModel(rings)
        }
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

    @RequiresApi(Build.VERSION_CODES.Q)
    private fun initRingsObserver() {
        modelName.let { partNo -> ringViewModel.getRings(partNo) }
        ringViewModel.rings.observe(viewLifecycleOwner) { rings ->

            binding.ringimgevie.setRingsToDraw(rings)
            setUpAddRingBtn(rings)
            ringRelatedListeners(rings)
            setUpRingAdapter(rings)
            setUpProcessBtnForRings(rings)

        }
    }

    private fun setUpRingAdapter(rings: ArrayList<Ring>) {
        adapterRingItem = AdapterRingItem(requireActivity(), rings)
        adapterRingItem.onItemClickListener = object : AdapterRingItem.OnItemClickListener {
            @RequiresApi(Build.VERSION_CODES.Q)
            override fun onEditBtnClick(
                position: Int,
                ring: Ring,
                rvModelCodeTblItemBinding: RvModelItemBinding
            ) {
                selectedRingPosition = position
                setSettingBtn(ring)
            }

            override fun onDeleteBtnClick(position: Int, ring: Ring) {
                initDeleteDialog(ring)
            }

            override fun onItemClick(
                position: Int,
                ring: Ring,
                rvModelCodeTblItemBinding: RvModelItemBinding
            ) {
                selectedRingPosition = position
            }

        }
        binding.rvRings.adapter = adapterRingItem
    }

    private fun initCameraListener(zoomRatio: Float) {

        binding.seekBar.progress = (zoomRatio * 10).toInt()
        binding.tvPercent.text = "${(zoomRatio * 10).toInt()}"
        seekBarChangedListeners()


    }

    private fun seekBarChangedListeners() {

        binding.seekBar.setOnSeekBarChangeListener(object : SeekBar.OnSeekBarChangeListener {
            override fun onProgressChanged(p0: SeekBar?, p1: Int, p2: Boolean) {

                zoomRatio = p1.toFloat() / 10
                Log.e("zoom ratio", "$zoomRatio")
                updateZoom(zoomRatio)

            }

            override fun onStartTrackingTouch(p0: SeekBar?) {

            }

            override fun onStopTrackingTouch(p0: SeekBar?) {
                //modelViewModel.updateZoom(modelsTbl.zoomRatio, modelsTbl.partNo)
                val sharedPreferences =
                    requireActivity().getSharedPreferences(
                        CommonMethods.COMMON_SHARED_PREFERENCE,
                        Context.MODE_PRIVATE
                    )

                sharedPreferences.edit().putFloat(CommonMethods.CAMERA_ZOOM_RATIO, zoomRatio)
                    .apply()
            }

        })
    }

    private fun initSharedP() {

        val sharedPreferences =
            requireActivity().getSharedPreferences(
                CommonMethods.COMMON_SHARED_PREFERENCE,
                Context.MODE_PRIVATE
            )

        zoomRatio = sharedPreferences.getFloat(CommonMethods.CAMERA_ZOOM_RATIO, 1.0f)

        binding.tvPercent.text = String.format("%.2f", zoomRatio)
        binding.seekBar.progress = (zoomRatio * 10).toInt()

        flashStatus = sharedPreferences.getBoolean(CommonMethods.FLASH_STATUS, false)

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

    private fun setUpCamera(zoomRatio: Float) {
        startCamera(zoomRatio)
        initCameraListener(zoomRatio)
    }

    private fun initDeleteDialog(ring: Ring) {


        val alertDialogBuilder = AlertDialog.Builder(requireActivity())
        alertDialogBuilder.setTitle("Alert")
        val warningsText = "Are you sure you want to <b>DELETE</b> Model?"
        val formattedText = Html.fromHtml(warningsText, Html.FROM_HTML_MODE_LEGACY)
        alertDialogBuilder.setMessage(formattedText)

        alertDialogBuilder.setPositiveButton("Yes") { dialog, _ ->

            CoroutineScope(Dispatchers.IO).launch {
                ring.syncStatus = CommonMethods.DELETE
                ringViewModel.updateRing(ring)

                requireActivity().runOnUiThread {
                    dialog.dismiss()
                }
                if (selectedRingPosition > 0) {
                    selectedRingPosition -= 1
                }

                ringViewModel.getRings(modelName)
            }

        }

        // Set negative button (No button) click listener
        alertDialogBuilder.setNegativeButton("No") { dialog, _ ->
            dialog.dismiss()
        }

        // Create and show the dialog
        val alertDialog = alertDialogBuilder.create()
        alertDialog.show()

    }

    private fun addRingsInModel(rings: ArrayList<Ring>) {

        val ring: Ring
        if (rings.isEmpty()) {
            ring = Ring(
                0,
                modelName,
                0,
                syncStatus = INSERT
            )
        } else {
            ring = rings.last()
            ring.id = 0
            ring.position += 1
            ring.syncStatus = INSERT

        }

        ringViewModel.insertRing(
            ring
        )

        Thread.sleep(200)
        modelName.let { it1 -> ringViewModel.getRings(it1) }
        // (requireActivity().application as ApplicationClass).ringsSubmission()
    }

    private fun getOutputDirectory(): File {
        //todo requireActivity() commented code is taking time to click photo
//        val mediaDir = externalMediaDirs.firstOrNull()?.let {
//            File(it, resources.getString(R.string.app_name)).apply { mkdirs() }
//        }
//        return if (mediaDir != null && mediaDir.exists()) mediaDir
//        else filesDir
        return requireActivity().filesDir
    }


    /*
        private fun setUpGreaterLessSpinners(binding: DialogRingSettingPixelrangeBinding, ring: Ring) {
            val glItems = arrayOf(
                ring.modelSetPointTo,
                if(ring.modelSetPointTo == Ring.GREATER_THAN)Ring.LESS_THAN
                else{
                    Ring.GREATER_THAN
                }
            ) // Replace with your actual items

            val greaterLessSpinnerAdaptor: ArrayAdapter<String> = ArrayAdapter(
                requireActivity(),
                android.R.layout.simple_spinner_item,
                glItems
            )
            binding.greaterLessSpinner.setSelection(
                when(ring.modelSetPointTo){
                    Ring.GREATER_THAN ->0
                    Ring.LESS_THAN ->1
                    else->0
                }
            )
            greaterLessSpinnerAdaptor.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item)
            binding.greaterLessSpinner.adapter = greaterLessSpinnerAdaptor
        }
    */

    /*
        private fun setUpGreaterLessSpinnerSelection(ringSettingPixelrangeBinding: DialogRingSettingPixelrangeBinding,ring: Ring?) {
            if(ring == null)return
            ringSettingPixelrangeBinding.greaterLessSpinner.onItemSelectedListener =
                object : AdapterView.OnItemSelectedListener {
                    override fun onItemSelected(
                        parent: AdapterView<*>,
                        view: View,
                        position: Int,
                        id: Long
                    ) {
                        when (parent.getItemAtPosition(position).toString()) {

                            Ring.GREATER_THAN -> {
                               ring.modelSetPointTo = Ring.GREATER_THAN
                            }

                            Ring.LESS_THAN -> {
                                ring.modelSetPointTo = Ring.LESS_THAN
                            }
                        }
                    }

                    override fun onNothingSelected(parent: AdapterView<*>) {

                    }
                }
        }
    */
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == TAKE_PHOTO_CODE && resultCode == Activity.RESULT_OK && data != null) {
            val selectedImageUri = data.data
            selectedImageUri?.let {
                binding.imagePreview.visibility = View.VISIBLE
                binding.cameraPreview.visibility = View.INVISIBLE
                binding.seekBar.visibility = View.INVISIBLE
                binding.tvPercent.visibility = View.INVISIBLE
                binding.btnCamera.visibility = View.INVISIBLE
                binding.btnProcess.visibility = View.VISIBLE
                binding.btnReCamera.visibility = View.VISIBLE
                binding.imagePreview.setImageURI(it) // assuming imageView is the id of your ImageView in XML
            }
        }
    }

    @RequiresApi(Build.VERSION_CODES.Q)
    @SuppressLint("ClickableViewAccessibility")
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


        binding.cameraFlashButton.setOnClickListener { changeFlash(flashStatus) }


        binding.root.setOnClickListener {}
    }

    private fun setUpServerResponseListener(
    ): ServerData.Companion.ServerResponseUIHandler {

        return object : ServerData.Companion.ServerResponseUIHandler {

            override fun onAllDataAdded() {
                mt(requireActivity(), "Data updated successfully!")
            }

            override fun onResponseFailure(erroeCode: Int, message: String) {
                mt(requireActivity(), "Failed to update!")
            }
        }
    }

    private fun changeFlash(flashStatus: Boolean) {
        camera?.cameraControl?.enableTorch(!flashStatus)
        // TODO:save value in shared preferences
        val sharedPreferences = requireActivity().getSharedPreferences(
            CommonMethods.COMMON_SHARED_PREFERENCE,
            Context.MODE_PRIVATE
        )
        val editor = sharedPreferences.edit()
        editor.putBoolean(CommonMethods.FLASH_STATUS, !flashStatus)
        editor.apply()
        this.flashStatus = !flashStatus

        when (!flashStatus) {
            false -> binding.cameraFlashButton.setImageResource(R.drawable.ic_flash_off_24)
            true -> binding.cameraFlashButton.setImageResource(R.drawable.ic_flash_on_24)
        }
    }


    private fun showResultsForRings(resultList: MutableList<ColorDetectionResult>) {
        requireActivity().runOnUiThread {
            val resultDialogBinding = DialogResultBinding.inflate(layoutInflater)
            resultDialogBinding.rvResult.layoutManager =
                LinearLayoutManager(requireActivity())
            val adapterResult = AdapterIntResult(requireActivity(), resultList)

            resultDialogBinding.rvResult.adapter = adapterResult
            //todo set difference
//                    if(resultList.size>1){
//                        val diff=resultList[0].retult+resultList[1].retult+resultList[2].retult
            /*resultDialogBinding.tvDifference.text =
                ("Avg: ${String.format("%.2f", avgCount)}")*/
//                        binding.tvResult.setText("$diff")
//                    }
            val resultDialog = Dialog(requireActivity())
            resultDialog.setContentView(resultDialogBinding.root)
            resultDialogBinding.btnClose.setOnClickListener {
                resultDialog.dismiss()
            }
            resultDialog.setCancelable(false)
            resultDialog.show()
            Log.e("resultSize", "${resultList.size}")
            Log.e("resultList", resultList.toString())
        }
    }

    private fun setUpProcessBtnForRings(rings: ArrayList<Ring>) {
        binding.btnProcess.setOnClickListener {
            binding.imagePreview.post {
                showResultsForRings(getResultsForRing(rings, binding.imagePreview.drawToBitmap()))
            }
            CoroutineScope(Dispatchers.IO).launch {
                /*delay(500)
                if (!MainActivity.isRingSubmissionRunning) {
                    ringViewModel.submitRingToServer(
                        MainActivity.getRingSubmissionHandler(
                            requireActivity()
                        )
                    )
                    MainActivity.isRingSubmissionRunning = false
                }*/

            }
        }
    }

    @SuppressLint("ClickableViewAccessibility")
    @RequiresApi(Build.VERSION_CODES.Q)
    private fun ringRelatedListeners(rings: ArrayList<Ring>) {


        if (binding.btnReCamera.visibility == View.INVISIBLE) {
            binding.cameraPreview.visibility = View.VISIBLE
            binding.imagePreview.visibility = View.INVISIBLE
            binding.seekBar.visibility = View.VISIBLE
            binding.tvPercent.visibility = View.VISIBLE
        }


        binding.btnCamera.setOnClickListener {
            if (rings.size != 0) {
                rings[selectedRingPosition].syncStatus = UPDATE
                ringViewModel.updateRing(rings[selectedRingPosition])
                Thread.sleep(300)
                //(requireActivity().application as ApplicationClass).ringsSubmission()
                takePhoto()
                binding.btnCamera.visibility = View.INVISIBLE
            }
        }



        if (rings.size != 0) {
            binding.ringimgevie.setOnTouchListener { _, event ->
                when (event.action) {
                    MotionEvent.ACTION_DOWN -> {
                        rings[selectedRingPosition].centerX = event.x
                        rings[selectedRingPosition].centerY = event.y
                        true
                    }

                    MotionEvent.ACTION_MOVE -> {
                        // Update circle coordinates based on touch position
                        rings[selectedRingPosition].centerX = event.x
                        rings[selectedRingPosition].centerY = event.y
                        binding.ringimgevie.setRingsToDraw(
                            rings
                        )
                        // Redraw the circle overlay with the updated coordinates

                        // Return true to indicate that the touch event has been handled
                        true
                    }

                    MotionEvent.ACTION_UP -> {
                        rings[selectedRingPosition].centerX = event.x
                        rings[selectedRingPosition].centerY = event.y

                        updateRingWithView(rings)
                        true
                    }

                    else -> false
                }
            }

            setUpSeekBarsForRings(rings)
        }
    }

    private fun updateRingWithView(rings: ArrayList<Ring>) {
        binding.ringimgevie.setRingsToDraw(
            rings
        )
        rings[selectedRingPosition].syncStatus = UPDATE
        ringViewModel.updateRing(rings[selectedRingPosition])
    }

    private fun setUpSeekBarsForRings(rings: ArrayList<Ring>) {

        val viewWidth = binding.ringimgevie.width
        val viewHeight = binding.ringimgevie.height
        binding.bottomSeekBar.setOnSeekBarChangeListener(object : SeekBar.OnSeekBarChangeListener {
            override fun onProgressChanged(p0: SeekBar?, p1: Int, p2: Boolean) {
                binding.tvBSeekBarValue.text = "$p1%"
                if (rings.size >= selectedRingPosition && rings.size > 0) {
                    val position = ((viewWidth) / 100) * p1
                    rings[selectedRingPosition].centerX = position.toFloat()
                    updateRingWithView(rings)
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
                if (rings.size > 0) {
                    val position = ((viewHeight) / 100) * p1
                    rings[selectedRingPosition].centerY = position.toFloat()
                    updateRingWithView(rings)
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


    private fun startCamera(zoomRatio: Float) {

        binding.btnProcess.visibility = View.INVISIBLE
        binding.cameraPreview.visibility = View.VISIBLE
        binding.seekBar.visibility = View.VISIBLE
        binding.tvPercent.visibility = View.VISIBLE

        mstCommCSViewModel.mstCommCSValues.observe(requireActivity()) {

            serverImpl = object : WifiUtils.ServerImplementation {
                override fun onReceive(msg: Int) {
                    if (msg == 1) {
                        takePhoto()
                    }
                }

                override fun onStart() {
                }

                override fun onStop(message: String) {

                }

            }

            portNo = it[0].port
            ipAddressCs = it[0].ipAddress
            Log.e("socket", "$portNo $ipAddressCs")

            if (server == null) {
                server = WifiUtils().Server(9090, serverImpl!!)
                if (server?.isAlive == false)
                    server?.start()
                wifiUtils.Client(ipAddressCs, portNo).sendMessage(2)
            }
        }

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

                    updateZoom(zoomRatio)
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

                    Toast.makeText(requireActivity(), msg, Toast.LENGTH_SHORT).show()
                    Log.d(TAG, msg)
                }
            })
        Log.e("output directory", outputDirectory.absolutePath)


    }

    @RequiresApi(Build.VERSION_CODES.Q)
    private fun setSettingBtn(ring: Ring?) {
        if (ring == null) {
            mt(requireActivity(), "Select A Ring First! ")
            return
        }

        binding.btnProcess.visibility = View.INVISIBLE
        binding.btnCamera.visibility = View.VISIBLE
        binding.btnReCamera.visibility = View.INVISIBLE
        binding.imagePreview.visibility = View.INVISIBLE
        binding.cameraPreview.visibility = View.VISIBLE
        binding.seekBar.visibility = View.VISIBLE
        binding.tvPercent.visibility = View.VISIBLE


        val dialogBinding = DialogRingSettingPixelrangeBinding.bind(
            LayoutInflater.from(requireActivity())
                .inflate(R.layout.dialog_ring_setting_pixelrange, null)
        )
        val dialog = Dialog(requireActivity())
        //setUpGreaterLessSpinners(dialogBinding, ring)/
        dialog.setContentView(dialogBinding.root)
        dialogBinding.edtInnerRadius.setText("${(ring.innerRadius).toInt()}")
        dialogBinding.edtOuterRadius.setText("${(ring.outerRadius).toInt()}")
        dialogBinding.edtPortions.setText("${(ring.portionCount)}")
        dialogBinding.etRgbSetPointFrom.setText("${ring.modelSetPointFrom}")
        dialogBinding.etRgbSetPointTo.setText("${ring.modelSetPointTo}")

        // for greater less selection

        // setUpGreaterLessSpinnerSelection(dialogBinding, ring)


        val rgbFrom = "${ring.rFrom},${ring.gFrom},${ring.bFrom}"
        val rgbTo = "${ring.rTo},${ring.gTo},${ring.bTo}"

        dialogBinding.etRgbFrom.setText(rgbFrom)
        dialogBinding.etRgbTo.setText(rgbTo)



        dialogBinding.btnSubmit.setOnClickListener {

            val strRangeFrom = dialogBinding.etRgbFrom.text.toString()
            val strRangeTo = dialogBinding.etRgbTo.text.toString()

            val arrRangeFrom = strRangeFrom.split(",")
            val arrRangeTo = strRangeTo.split(",")

            if (arrRangeFrom.size < 3 || arrRangeTo.size < 3) {
                Toast.makeText(requireActivity(), "Please Enter Valid Range", Toast.LENGTH_SHORT)
                    .show()
                return@setOnClickListener
            }
            try {


                for (i in arrRangeFrom.indices) {
                    if (arrRangeFrom[i].toInt() < 0 || arrRangeTo[i].toInt() > 255) {
                        Toast.makeText(
                            requireActivity(),
                            "Please Enter Valid Range",
                            Toast.LENGTH_SHORT
                        ).show()
                        return@setOnClickListener
                    }
                }


            } catch (e: NumberFormatException) {
                Toast.makeText(
                    requireActivity(),
                    "Please Enter Valid Range",
                    Toast.LENGTH_SHORT
                ).show()
                return@setOnClickListener
            }

            if (TextUtils.isEmpty(strRangeFrom)) {
                Toast.makeText(requireActivity(), "Please Enter Range", Toast.LENGTH_SHORT)
                    .show()
                return@setOnClickListener
            }
            if (TextUtils.isEmpty(strRangeTo)) {
                Toast.makeText(requireActivity(), "Please Enter Range", Toast.LENGTH_SHORT)
                    .show()
                return@setOnClickListener
            }

            if (TextUtils.isEmpty(dialogBinding.edtInnerRadius.text.toString())) {
                Toast.makeText(
                    requireActivity(),
                    "Please Enter inner radius",
                    Toast.LENGTH_SHORT
                )
                    .show()
                return@setOnClickListener
            }

            if (TextUtils.isEmpty(dialogBinding.edtOuterRadius.text.toString())) {
                Toast.makeText(
                    requireActivity(),
                    "Please Enter outer radius",
                    Toast.LENGTH_SHORT
                )
                    .show()
                return@setOnClickListener
            }

            if (TextUtils.isEmpty(dialogBinding.edtPortions.text.toString())) {

                Toast.makeText(
                    requireActivity(),
                    "Please Enter no of portions",
                    Toast.LENGTH_SHORT
                )
                    .show()
                return@setOnClickListener
            }

            if (TextUtils.isEmpty(dialogBinding.etRgbSetPointFrom.text.toString())) {

                Toast.makeText(
                    requireActivity(),
                    "Please Enter set point From",
                    Toast.LENGTH_SHORT
                )
                    .show()
                return@setOnClickListener
            }

            if (TextUtils.isEmpty(dialogBinding.etRgbSetPointTo.text.toString())) {

                Toast.makeText(
                    requireActivity(),
                    "Please Enter set point To",
                    Toast.LENGTH_SHORT
                )
                    .show()
                return@setOnClickListener
            }

            if (dialogBinding.edtPortions.text.toString().toInt() < 1) {

                Toast.makeText(
                    requireActivity(),
                    "At least 1 Portion required",
                    Toast.LENGTH_SHORT
                )
                    .show()
                return@setOnClickListener
            }



            if (dialogBinding.edtInnerRadius.text.toString()
                    .toFloat() > dialogBinding.edtOuterRadius.text.toString().toFloat()
            ) {

                mt(
                    requireActivity(),
                    "Outer Radius should be greater that inner radius!",
                )
                return@setOnClickListener

            }


            ring.rFrom = arrRangeFrom[0].toInt()
            ring.gFrom = arrRangeFrom[1].toInt()
            ring.bFrom = arrRangeFrom[2].toInt()

            ring.rTo = arrRangeTo[0].toInt()
            ring.gTo = arrRangeTo[1].toInt()
            ring.bTo = arrRangeTo[2].toInt()




            ringViewModel.updateRing(

                Ring(
                    ring.id,
                    ring.modelId,
                    ring.position,
                    ring.centerX,
                    ring.centerY,
                    dialogBinding.edtInnerRadius.text.toString().toFloat(),
                    dialogBinding.edtOuterRadius.text.toString().toFloat(),
                    dialogBinding.edtPortions.text.toString().toInt(),
                    arrRangeFrom[0].toInt(),
                    arrRangeFrom[1].toInt(),
                    arrRangeFrom[2].toInt(),
                    arrRangeTo[0].toInt(),
                    arrRangeTo[1].toInt(),
                    arrRangeTo[2].toInt(),
                    dialogBinding.etRgbSetPointFrom.text.toString().toInt(),
                    dialogBinding.etRgbSetPointTo.text.toString().toInt(),
                    ring.zoomRatio,
                    UPDATE

                )
            )
            Thread.sleep(200)

            // (requireActivity().application as ApplicationClass).ringsSubmission()

            ringViewModel.getRings(ring.modelId)

            dialog.dismiss()
        }


        dialog.show()
    }


    //requireActivity() is for boxes
    private fun initBoxObserver() {

        boundingBoxViewModelCD.getOnlyBoundingBoxes().observe(viewLifecycleOwner) { boxes ->
            binding.btnCamera.setOnClickListener {
                Thread.sleep(300)
                //(requireActivity().application as ApplicationClass).ringsSubmission()
                takePhoto()
                binding.btnCamera.visibility = View.INVISIBLE
                boundingBoxViewModelCD.updateBoundingBoxTable(setUpServerResponseListener(), boxes)

            }
        }

        boundingBoxViewModelCD.getBoundingBoxesWithModel(modelName)

        boundingBoxViewModelCD.boundingBoxesWithModel.observe(viewLifecycleOwner) { boxes ->
            binding.ringimgevie.setBoxesToDraw(boxes)
            initBoxesAdapter(boxes)
            setUpSeekBarsForBoxes(boxes)
            setUpAddBtnForBoxes(boxes)
            setUpProcessBtnForBoxes(boxes)
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
                Toast.makeText(requireActivity(), "Please Enter Height", Toast.LENGTH_SHORT)
                    .show()
                return@setOnClickListener
            }

            if (TextUtils.isEmpty(widthString)) {
                Toast.makeText(requireActivity(), "Please Enter Width", Toast.LENGTH_SHORT)
                    .show()
                return@setOnClickListener
            }

            if (TextUtils.isEmpty(strPixelRange)) {
                Toast.makeText(
                    requireActivity(),
                    "Please Enter Pixel Range",
                    Toast.LENGTH_SHORT
                )
                    .show()
                return@setOnClickListener
            }
            if (TextUtils.isEmpty(strC1RangeFrom)) {
                Toast.makeText(requireActivity(), "Please Enter Range", Toast.LENGTH_SHORT)
                    .show()
                return@setOnClickListener;
            }
            if (TextUtils.isEmpty(strC1RangeTo)) {
                Toast.makeText(requireActivity(), "Please Enter Range", Toast.LENGTH_SHORT)
                    .show()
                return@setOnClickListener;
            }
            if (TextUtils.isEmpty(strC2RangeFrom)) {
                Toast.makeText(requireActivity(), "Please Enter Range", Toast.LENGTH_SHORT)
                    .show()
                return@setOnClickListener;
            }
            if (TextUtils.isEmpty(strC2RangeTo)) {
                Toast.makeText(requireActivity(), "Please Enter Range", Toast.LENGTH_SHORT)
                    .show()
                return@setOnClickListener;
            }
            if (TextUtils.isEmpty(c1IgnorePixel)) {
                Toast.makeText(
                    requireActivity(),
                    "Please Enter C1 Ignore Pixels",
                    Toast.LENGTH_SHORT
                ).show()
                return@setOnClickListener;
            }
            if (TextUtils.isEmpty(c2IgnorePixel)) {

                mt(
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
                mt(
                    requireActivity(),
                    "Please Enter Valid Range"
                )

                return@setOnClickListener
            }
            if (arrC2RangeFrom.size < 3 || arrC2RangeTo.size < 3) {
                Toast.makeText(
                    requireActivity(),
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
                    requireActivity(),
                    "Please Enter Valid Range",
                    Toast.LENGTH_SHORT
                )
                    .show()
            }
            if (arrC1RangeFrom.size < 3 || arrC1RangeTo.size < 3) {
                Toast.makeText(
                    requireActivity(),
                    "Please Enter Valid Range",
                    Toast.LENGTH_SHORT
                )
                    .show()
                return@setOnClickListener;
            }
            if (arrC2RangeFrom.size < 3 || arrC2RangeTo.size < 3) {
                Toast.makeText(
                    requireActivity(),
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
                        modelId = modelName,
                        position = 1,
                        syncStatus = false
                    )
                }
                boundingBoxViewModelCD.insert(
                    box
                )

                withContext(Dispatchers.Main) {
                    boundingBoxViewModelCD.getBoundingBoxesWithModel(modelName)
                }
            }

        }
    }

    private fun setUpProcessBtnForBoxes(boxes: ArrayList<BoundingBoxTableCD>) {
        binding.btnProcess.setOnClickListener {
            val bitmap = binding.imagePreview.drawToBitmap()

            try {
                showResults(getResultsForBoxes(boxes, bitmap, bitmap))
                //showResults(getResultsForLineBoxes(boxes, bitmap, bitmap))
            } catch (_: UninitializedPropertyAccessException) {
                showResults(getResultsForBoxes(boxes, bitmap, bitmap))
                //showResults(getResultsForLineBoxes(boxes, bitmap, bitmap))
                mt(requireActivity(), "Capture Image First")
            }
            CoroutineScope(Dispatchers.IO).launch {
                delay(500)
                /*if (!MainActivity.isBoundingBoxSubmissionRunning) {
                    boundingBoxViewModel.updateBoundingBoxTable(
                        MainActivity.getBoundingBoxSubmissionHandler(
                            requireActivity()
                        )
                    )
                    MainActivity.isBoundingBoxSubmissionRunning = false
                }*/

            }
        }
    }

    private fun showResults(resultList: MutableList<ColorDetectionResult>) {
        requireActivity().runOnUiThread {
            val resultDialogBinding = DialogResultBinding.inflate(layoutInflater)
            resultDialogBinding.rvResult.layoutManager =
                LinearLayoutManager(requireActivity())
            val adapterResult = AdapterIntResult(requireActivity(), resultList)

            resultDialogBinding.rvResult.adapter = adapterResult
            //todo set difference
//                    if(resultList.size>1){
//                        val diff=resultList[0].retult+resultList[1].retult+resultList[2].retult
            /*resultDialogBinding.tvDifference.text =
                ("Avg: ${String.format("%.2f", avgCount)}")*/
//                        binding.tvResult.setText("$diff")
//                    }
            val resultDialog = Dialog(requireActivity())

            resultDialog.setContentView(resultDialogBinding.root)
            resultDialogBinding.btnClose.setOnClickListener {
                resultDialog.dismiss()
            }

            resultDialog.setCancelable(false)
            resultDialog.show()

            Log.e("resultSize", "${resultList.size}")
            Log.e("resultList", resultList.toString())
        }
    }

    private fun deleteBoundingBox(box: BoundingBoxTableCD) {
        //refresh overlayView when bounding box is deleted
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


    /*private fun setCircleDiam() {

        circle = Circle(200f, 450f, 400f)
        binding.circleOverlay.setCircle(circle.centerX, circle.centerY, circle.radius)

    }*/


    private fun checkPermissions(): Boolean {
        var result: Int
        val listPermissionsNeeded: MutableList<String> = ArrayList()
        for (p in permissions) {
            result = ContextCompat.checkSelfPermission(requireActivity().applicationContext, p)
            if (result != PackageManager.PERMISSION_GRANTED) {
                listPermissionsNeeded.add(p)
            }
        }
        if (listPermissionsNeeded.isNotEmpty()) {
            ActivityCompat.requestPermissions(
                requireActivity(),
                listPermissionsNeeded.toTypedArray(),
                10
            )
            return false
        }
        return true
    }

    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
    }


    override fun onStart() {
        super.onStart()
        checkPermissions()
    }

    /*fun cropBitmapToCircle(originalBitmap: Bitmap, centerX: Float, centerY: Float, radius: Float): Bitmap {
        // Calculate the bounding box for the circle
        val left = centerX - radius
        val top = centerY - radius
        val right = centerX + radius
        val bottom = centerY + radius

        // Create a new Bitmap to hold the cropped circle
        val outputBitmap = Bitmap.createBitmap((radius * 2).toInt(), (radius * 2).toInt(), Bitmap.Config.ARGB_8888)

        // Create a canvas with the new Bitmap
        val canvas = Canvas(outputBitmap)

        // Create a shader for the original Bitmap
        val shader = BitmapShader(originalBitmap, Shader.TileMode.CLAMP, Shader.TileMode.CLAMP)

        // Create a Paint object to draw the Bitmap with the shader
        val paint = Paint()
        paint.shader = shader

        // Create a Path for the circular region to be cropped
        val path = Path()

        // Add a circle to the Path with the given center and radius
        path.addCircle(radius, radius, radius, Path.Direction.CCW)

        // Set the path as the clipping region for the canvas
        canvas.clipPath(path)

        // Draw the original Bitmap onto the canvas with the circular clipping
        canvas.drawBitmap(originalBitmap, Rect(left.toInt(), top.toInt(), right.toInt(), bottom.toInt()), RectF(centerX-ring.outerRadius, centerY-ring.outerRadius, centerX + ring.outerRadius, centerY+ring.outerRadius), paint)

        // Release any resources associated with the original Bitmap
        originalBitmap.recycle()

        return outputBitmap
    }*/

    override fun onDestroy() {
        super.onDestroy()
        Log.e("lifecycle", "onPause")
        server?.stopServer()
    }

    override fun onResume() {
        super.onResume()
        updateZoom(zoomRatio)
    }


    companion object {
        const val TAKE_PHOTO_CODE = 1
        const val SCAN_QR_CODE = 2

        private var isSettable: Int? = null

        //requireActivity() method return the pixel values for each portion for given rgb range of spring
        private fun countPixelsInRingPortions(ring: Ring, bitmap: Bitmap): IntArray {
            //val rgbRange = 255..255
            val portionPixelsCount = IntArray(ring.portionCount)

            val centerX = ring.centerX
            val centerY = ring.centerY


            var count = 0

            for (x in 0 until bitmap.width) {
                for (y in 0 until bitmap.height) {
                    val distanceFromCenter = sqrt(
                        (x - centerX).toDouble().pow(2.0) +
                                (y - centerY).toDouble().pow(2.0)
                    ).toFloat()

                    if (distanceFromCenter in ring.innerRadius..ring.outerRadius) {
                        // Calculate the angle of the pixel from the center
                        val angle =
                            Math.toDegrees(
                                atan2(
                                    (y - centerY).toDouble(),
                                    (x - centerX).toDouble()
                                )
                            )
                        val normalizedAngle = (angle + 360) % 360

                        // Determine the portion index based on the angle
                        val portionIndex = ((normalizedAngle / 360) * ring.portionCount).toInt()

                        //val pixelColor = bitmap.getPixel(x, y)

                        // Check if the pixel color falls within the specified RGB range
                        val pixelColor = bitmap.getColor(x, y).toArgb()

                        count++

                        val red = Color.red(pixelColor)
                        val green = Color.green(pixelColor)
                        val blue = Color.blue(pixelColor)


                        //portionPixelsCount[portionIndex]++

                        if (red in ring.rFrom..ring.rTo && green in ring.gFrom..ring.gTo && blue in ring.bFrom..ring.bTo) {
                            portionPixelsCount[portionIndex]++
                        }

                    }
                }
            }


            return portionPixelsCount
        }

        //requireActivity() method returns the results for single ring
        private fun getResultsForSingleRing(ring: Ring, bitmap: Bitmap): ColorDetectionResult {

            val portionResultList = countPixelsInRingPortions(ring, bitmap)
            //pixelCountAdaptor = PixelCountAdaptor(portionResultList)

            return ColorDetectionResult(
                ring.modelId + ring.position,
                portionResultList.sum(),
                portionResultList.average(),
                portionResultList.minOrNull() ?: 0,
                portionResultList.maxOrNull() ?: 0,
                portionResultList.toCollection(ArrayList()),
                0,
                0.0,
                0,
                0,
                ArrayList(0)
            )
        }

        //requireActivity() method returns the results for all rings for that model
        fun getResultsForRing(
            rings: ArrayList<Ring>,
            bitmap: Bitmap
        ): ArrayList<ColorDetectionResult> {
            val results = ArrayList<ColorDetectionResult>()

            for (ring in rings) {
                results.add(getResultsForSingleRing(ring, bitmap))
            }

            return results
        }

        fun getResultsForBoxes(
            boxes: ArrayList<BoundingBoxTableCD>,
            bitmap: Bitmap,
            previewBitmap: Bitmap
        ): ArrayList<ColorDetectionResult> {
            Log.e("tag", "bitmap height: ${bitmap.height}")

            val resultList = ArrayList<ColorDetectionResult>()

            val ratio = bitmap.height.toFloat() / previewBitmap.height.toFloat()
            Log.e("BitmapDetails", "Bitmaps Detail : H-${bitmap.height}, W-${bitmap.width}")
            Log.e(
                "BitmapDetails",
                "Preview Detail : H-${previewBitmap.height}, W-${previewBitmap.width}"
            )
            Log.e("BitmapDetails", "Ratio Detail : R-${ratio}")
            /* val dialogBinding = DialogPleaseWaitBinding.inflate(layoutInflater)
             val dialog = Dialog(requireActivity())
             dialog.setContentView(dialogBinding.root)
             dialog.setCancelable(true)
             dialog.show()*/

            if (boxes.size > 0) {

                for (detection in boxes) {
                    resultList.add(
                        //processing single box here and adding result to resultList
                        getResultForSingleBox(detection, bitmap, ratio)

                    )
                }
            }

            //dialog.dismiss()
            return resultList
        }

        fun getResultsForLineBoxes(
            boxes: ArrayList<BoundingBoxTableCD>,
            bitmap: Bitmap,
            previewBitmap: Bitmap
        ): ArrayList<ColorDetectionResult> {
            Log.e("tag", "bitmap height: ${bitmap.height}")

            val resultList = ArrayList<ColorDetectionResult>()
            val ratio = bitmap.height.toFloat() / previewBitmap.height.toFloat()

            Log.e("BitmapDetails", "Bitmaps Detail : H-${bitmap.height}, W-${bitmap.width}")
            Log.e(
                "BitmapDetails",
                "Preview Detail : H-${previewBitmap.height}, W-${previewBitmap.width}"
            )
            Log.e("BitmapDetails", "Ratio Detail : R-${ratio}")

            if (boxes.isNotEmpty()) {
                for (box in boxes) {
                    // Calculate original dimensions
                    val originalWidth = box.right - box.left
                    val originalHeight = box.bottom - box.top

                    // Calculate middle 50% range for width
                    val startX = box.left + (originalWidth * 0.35).toInt()
                    val endX = box.left + (originalWidth * 0.65).toInt()

                    // Height of new boxes (double the original height)
                    val newBoxHeight = originalHeight * 2

                    // Total number of new boxes (odd number)
                    val numberOfBoxes = box.c1PixelCountRange // Adjust this value as needed

                    // Distance between each narrow box
                    val spacing = (endX - startX) / (numberOfBoxes - 1)

                    for (i in 0 until numberOfBoxes) {
                        // Calculate x-coordinate for the narrow box
                        val boxX = startX + (i * spacing)

                        // Calculate new top and bottom for the box
                        val boxTop = box.top - (newBoxHeight / 2)
                        val boxBottom = box.bottom + (newBoxHeight / 2)

                        // Create a new narrow box
                        val newBox = BoundingBoxTableCD(
                            id = 0,
                            modelId = "",
                            position = i,
                            left = boxX,
                            right = boxX + 1, // 1-pixel wide box
                            top = boxTop,
                            bottom = boxBottom,
                            c1_r_from = box.c1_r_from,
                            c1_g_from = box.c1_g_from,
                            c1_b_from = box.c1_b_from,
                            c2_r_from = box.c1_r_from,
                            c2_g_from = box.c2_g_from,
                            c2_b_from = box.c2_b_from,
                            c1_r_to = box.c1_r_to,
                            c1_g_to = box.c1_g_to,
                            c1_b_to = box.c1_b_to,
                            c2_r_to = box.c2_r_to,
                            c2_g_to = box.c2_g_to,
                            c2_b_to = box.c2_b_to,
                            syncStatus = false

                        )

                        // Process the new box and add the result to the result list
                        resultList.add(getResultForSingleBox(newBox, bitmap, ratio))
                    }
                }
            }

            return resultList
        }


        private fun getResultForSingleBox(
            box: BoundingBoxTableCD,
            bitmap: Bitmap,
            ratio: Float
        ): ColorDetectionResult {
            val pixelsList = ArrayList<Pair<String, Int>>()
            var c1PitchCount = 0
            var c2PitchCount = 0
            var isC1 = false
            var isC2 = false

            var c1Counter = 0
            var c2Counter = 0
            var areaCount = 0
            val left = (box.left * ratio).toInt()+1
            val right = (box.right * ratio).toInt()
            val top = (box.top * ratio).toInt()+1
            val bottom = (box.bottom * ratio).toInt()
            Log.e("BBOX Details", "l-$left, R-$right, T-$top, B-$bottom")
            for (x in (left)..right) {
                for (y in (top)..bottom) {
                    if (y > bitmap.height || x > bitmap.width)
                        break
                    try {
                        val color1 = bitmap.getColor(x, y).toArgb()
                        val r = Color.red(color1)
                        val g = Color.green(color1)
                        val b = Color.blue(color1)

                        if (r >= box.c1_r_from && r <= box.c1_r_to && g >= box.c1_g_from && g <= box.c1_g_to && b >= box.c1_b_from && b <= box.c1_b_to) {
                            c1Counter++
                            isC1 = true
                            c1PitchCount++

                            if (isC2) {

                                if (box.c2PixelCountRange < c2PitchCount)
                                    pixelsList.add(Pair("c2", c2PitchCount))

                                c2PitchCount = 0
                                isC2 = false

                            }

                        } else if (r >= box.c2_r_from && r <= box.c2_r_to && g >= box.c2_g_from && g <= box.c2_g_to && b >= box.c2_b_from && b <= box.c2_b_to) {
                            c2Counter++
                            isC2 = true
                            c2PitchCount++

                            if (isC1) {

                                if (box.c1PixelCountRange < c1PitchCount)
                                    pixelsList.add(Pair("c1", c1PitchCount))

                                c1PitchCount = 0
                                isC1 = false
                            }

                        }
                        areaCount++
                    } catch (_: java.lang.Exception) {
                    } catch (_: Exception) {
                    }


                    /*if (r >= detection.r_from && r <= detection.r_to && g >= detection.g_from && g <= detection.g_to && b >= detection.b_from && b <= detection.b_to) {
                    counter++
                    if (isOther) {
                        roundsCounter++
                        requireActivity().runOnUiThread {
                            binding.tvRoundCount.text = (roundsCounter).toString()
                        }
                        isOther = false
                    }
                } else {
                    isOther = true
                }*/
                }

            }

            val c1PitchList = ArrayList<Int>()
            val c2PitchList = ArrayList<Int>()



            for (pixels in pixelsList) {
                if (pixels.first == "c1") {
                    c1PitchList.add(pixels.second)
                } else if (pixels.first == "c2") {
                    c2PitchList.add(pixels.second)
                }
            }

            val c1PitchIntArray = c1PitchList.toIntArray()
            val c2PitchIntArray = c2PitchList.toIntArray()

            val totalPixel = (right - left) * (bottom - top)

            return ColorDetectionResult(
                box.modelId + box.position,
                c1Counter,
                (c1Counter.toDouble() / totalPixel) * 100,
                c1PitchIntArray.minOrNull() ?: 0,
                c1PitchIntArray.maxOrNull() ?: 0,
                c1PitchList,
                c2Counter,
                (c2Counter.toDouble() / totalPixel) * 100,
                c2PitchIntArray.minOrNull() ?: 0,
                c2PitchIntArray.maxOrNull() ?: 0,
                c2PitchList,
                areaCount
            )
        }


    }


}
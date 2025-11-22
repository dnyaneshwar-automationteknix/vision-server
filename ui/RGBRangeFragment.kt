/*
package com.automationteknix.vision_app_3xo_n.colordetection.ui

import android.app.Dialog
import android.app.ProgressDialog
import android.os.Bundle
import android.text.Html
import androidx.fragment.app.Fragment
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.appcompat.app.AlertDialog
import androidx.fragment.app.viewModels
import androidx.lifecycle.Observer
import androidx.recyclerview.widget.LinearLayoutManager
import com.automationteknix.vision_app_3xo_n.ApplicationClass
import com.automationteknix.vision_app_3xo_n.utils.CommonMethods
import com.automationteknix.vision_app_3xo_n.MainActivity
import com.automationteknix.vision_app_3xo_n.R
import com.automationteknix.vision_app_3xo_n...RGBRangeAdapter
import com.automationteknix.vision_app_3xo_n.colordetection.database.rgbRange.entity.RGBRangeTable
import com.automationteknix.vision_app_3xo_n.colordetection.database.rgbRange.entity.RGBViewModel
import com.automationteknix.vision_app_3xo_n.databasenew.ViewModelFactory
import com.automationteknix.vision_app_3xo_n.databinding.DialogProgressBarBinding
import com.automationteknix.vision_app_3xo_n.databinding.DialogRgbRangeDetailsBinding
import com.automationteknix.vision_app_3xo_n.databinding.FragmentRGBRangeBinding
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

class RGBRangeFragment : Fragment() {

    private lateinit var binding: FragmentRGBRangeBinding
    private lateinit var adapter: RGBRangeAdapter
    private lateinit var progressDialog: Dialog
    private lateinit var progressBinding: DialogProgressBarBinding

    private val rgbViewModel: RGBViewModel by viewModels {
        ViewModelFactory((requireActivity().application as ApplicationClass).rgbRangeRepo)
    }

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        binding = FragmentRGBRangeBinding.inflate(layoutInflater)
        initRecyclerView()
        initDialog()
        initObserver()

        return binding.root
    }

//    private fun initRecyclerView() {
//        adapter = RGBRangeAdapter(requireContext(), emptyList())
//        binding.recyclerView.layoutManager = LinearLayoutManager(requireContext())
//        binding.recyclerView.adapter = adapter
//
//    }

    private fun initRecyclerView() {
        adapter = RGBRangeAdapter(requireContext(), emptyList())
        adapter.onItemClickListener = object : RGBRangeAdapter.OnItemClickListener {
            override fun onItemClick(rgbRangeTable: RGBRangeTable) {
                showDialog(rgbRangeTable)
            }

            override fun onDeleteBtnClick(position: Int, rgbRangeTable: RGBRangeTable) {
                initDeleteDialog(rgbRangeTable)            }
        }
        binding.recyclerView.layoutManager = LinearLayoutManager(requireContext())
        binding.recyclerView.adapter = adapter
    }
    private fun initObserver() {
        rgbViewModel.allRGBRanges.observe(viewLifecycleOwner, Observer { rgbRanges ->
            rgbRanges?.let { adapter.setRGBRanges(it) }
        })

    }
private  fun initDialog(){
    progressBinding = DialogProgressBarBinding.bind(
        LayoutInflater.from(requireContext())
            .inflate(R.layout.dialog_progress_bar, null)
    )
    progressDialog = ProgressDialog(requireContext())
    progressDialog.setContentView(progressBinding.root)
}

    private fun showDialog(rgbRangeTable: RGBRangeTable) {
        val dialogBinding = DialogRgbRangeDetailsBinding.inflate(LayoutInflater.from(context))
        val dialog = Dialog(requireContext())
        dialog.setContentView(dialogBinding.root)

        dialogBinding.nameTextView.text = rgbRangeTable.name
        dialogBinding.rFromTextView.text = "R From: ${rgbRangeTable.r_from}"
        dialogBinding.gFromTextView.text = "G From: ${rgbRangeTable.g_from}"
        dialogBinding.bFromTextView.text = "B From: ${rgbRangeTable.b_from}"
        dialogBinding.rToTextView.text = "R To: ${rgbRangeTable.r_to}"
        dialogBinding.gToTextView.text = "G To: ${rgbRangeTable.g_to}"
        dialogBinding.bToTextView.text = "B To: ${rgbRangeTable.b_to}"
        dialogBinding.closeButton.setOnClickListener {
            dialog.dismiss()
        }

        dialog.show()
    }
    private fun initDeleteDialog(rgbRangeTable: RGBRangeTable) {


        val alertDialogBuilder = AlertDialog.Builder(requireContext())
        alertDialogBuilder.setTitle("Alert")
        val warningsText = "Are you sure you want to <b>DELETE</b> Model?"
        val formattedText = Html.fromHtml(warningsText, Html.FROM_HTML_MODE_LEGACY)
        alertDialogBuilder.setMessage(formattedText)


        // Set positive button (Yes button) click listener
        alertDialogBuilder.setPositiveButton("Yes") { dialog, which ->


            CoroutineScope(Dispatchers.IO).launch {

                requireActivity().runOnUiThread {
                    progressDialog.show()
                    rgbRangeTable.syncStatus = CommonMethods.DELETE
                    rgbViewModel.update(rgbRangeTable)

                    if(!MainActivity.isRGBSubmissionRunning) {
                        rgbViewModel.updateRGBRange(
                            MainActivity.getRGBSubmissionHandler(
                                requireActivity()
                            )
                        )

                        MainActivity.isRGBSubmissionRunning = true
                    }
                }

                requireActivity().runOnUiThread {
                    progressDialog.dismiss()
                    dialog.dismiss()
                }

            }


        }

        // Set negative button (No button) click listener
        alertDialogBuilder.setNegativeButton("No") { dialog, which ->
            dialog.dismiss()
        }

        // Create and show the dialog
        val alertDialog = alertDialogBuilder.create()
        alertDialog.show()

    }


}*/
